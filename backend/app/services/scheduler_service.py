"""
Background task scheduler service

Handles scheduled background tasks like:
- Daily momentum recalculation
- Stalled project detection
- Daily urgency zone recalculation
- Future: notification sending, cleanup tasks
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.db_utils import ensure_tz_aware

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the global scheduler instance"""
    return _scheduler


async def momentum_recalculation_job():
    """
    Background job to recalculate momentum scores for all projects.

    This job:
    1. Updates momentum scores for all active projects
    2. Detects newly stalled projects
    3. Logs results to activity log
    """
    logger.info("Starting scheduled momentum recalculation")

    db: Session = SessionLocal()
    try:
        from app.services.intelligence_service import IntelligenceService

        # Update all momentum scores
        updated_count = IntelligenceService.update_all_momentum_scores(db)

        # Create momentum snapshots for trend/sparkline data (BETA-023)
        snapshot_count = IntelligenceService.create_momentum_snapshots(db)
        logger.info(f"Momentum snapshots created: {snapshot_count}")

        # Update all area health scores
        area_stats = IntelligenceService.update_all_area_health_scores(db)
        logger.info(f"Area health scores updated: {area_stats.get('updated', 0)} areas")

        # Detect stalled projects
        stalled_projects = IntelligenceService.detect_stalled_projects(db)
        newly_stalled = [p for p in stalled_projects if p.stalled_since and
                        (datetime.now(timezone.utc) - ensure_tz_aware(p.stalled_since)).days <= 1]

        logger.info(
            f"Momentum recalculation complete: "
            f"{updated_count} projects updated, "
            f"{len(stalled_projects)} total stalled, "
            f"{len(newly_stalled)} newly stalled"
        )

        # Log to activity log if there are newly stalled projects
        if newly_stalled:
            from app.models.activity_log import ActivityLog
            for project in newly_stalled:
                activity = ActivityLog(
                    entity_type="project",
                    entity_id=project.id,
                    action_type="stalled",
                    details={"days_inactive": settings.MOMENTUM_STALLED_THRESHOLD_DAYS},
                )
                db.add(activity)
            db.commit()
            logger.warning(f"Logged {len(newly_stalled)} newly stalled projects")

    except Exception as e:
        logger.error(f"Momentum recalculation failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


async def storage_change_detection_job():
    """
    Background job to detect external file changes (e.g. user edited in Obsidian)
    and update the SQLite cache accordingly.

    Only runs when STORAGE_MODE == "storage_first".
    """
    from app.services.storage_service import _is_storage_first

    if not _is_storage_first():
        return

    logger.debug("Checking for external storage changes")

    db: Session = SessionLocal()
    try:
        from app.services.storage_service import StorageService

        service = StorageService(db)
        stats = service.sync_external_changes()
        if stats.get("changes", 0) > 0:
            logger.info(f"External change sync: {stats}")
    except Exception as e:
        logger.error(f"External change detection failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


async def trial_expiry_job():
    """
    Daily job: downgrade expired reverse-trials to the free tier.

    Calls LicenseService.process_expired_trials() which finds every license
    where trial_expires_at < now AND activated_at IS NULL AND tier != 'free',
    sets tier = 'free', and commits.

    Without this job the reverse-trial promise never fires: users on day 15
    would silently keep full-tier access forever.
    """
    logger.info("Starting scheduled trial expiry processing")
    db: Session = SessionLocal()
    try:
        from app.services.license_service import LicenseService

        affected_ids = LicenseService.process_expired_trials(db)
        if affected_ids:
            logger.info(
                "Trial expiry: downgraded %d license(s) to free tier (user_ids=%s)",
                len(affected_ids),
                affected_ids,
            )
        else:
            logger.debug("Trial expiry: no expired trials found")
    except Exception as e:
        logger.error("Trial expiry job failed: %s", e, exc_info=True)
        db.rollback()
    finally:
        db.close()


async def urgency_zone_recalculation_job():
    """
    Background job to recalculate urgency zones for all active tasks.

    This ensures that tasks whose due dates have arrived or passed
    get promoted to Critical Now automatically, even without being edited.
    """
    logger.info("Starting scheduled urgency zone recalculation")

    db: Session = SessionLocal()
    try:
        from app.services.task_service import recalculate_all_urgency_zones

        updated_count = recalculate_all_urgency_zones(db)
        logger.info(f"Urgency zone recalculation complete: {updated_count} tasks updated")

    except Exception as e:
        logger.error(f"Urgency zone recalculation failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """
    Start the background task scheduler.

    Schedules:
    - Momentum recalculation: Daily at 2:00 AM (or per MOMENTUM_RECALCULATE_INTERVAL)
    - Urgency zone recalculation: Daily at 12:05 AM
    """
    global _scheduler

    if _scheduler is not None:
        logger.warning("Scheduler already running")
        return

    _scheduler = AsyncIOScheduler()

    # Schedule momentum recalculation
    recalc_interval = settings.MOMENTUM_RECALCULATE_INTERVAL

    if recalc_interval > 0:
        if recalc_interval >= 86400:  # 24 hours or more - use daily cron
            # Run daily at 2:00 AM
            _scheduler.add_job(
                momentum_recalculation_job,
                CronTrigger(hour=2, minute=0),
                id="momentum_recalculation",
                name="Daily Momentum Recalculation",
                replace_existing=True,
            )
            logger.info("Scheduled momentum recalculation: daily at 2:00 AM")
        else:
            # Use interval trigger for more frequent updates
            _scheduler.add_job(
                momentum_recalculation_job,
                IntervalTrigger(seconds=recalc_interval),
                id="momentum_recalculation",
                name="Periodic Momentum Recalculation",
                replace_existing=True,
            )
            logger.info(f"Scheduled momentum recalculation: every {recalc_interval} seconds")
    else:
        logger.info("Momentum recalculation scheduling disabled (interval=0)")

    # Schedule external storage change detection (Phase 3)
    # Only meaningful in storage_first mode; the job self-checks and no-ops in legacy mode
    _scheduler.add_job(
        storage_change_detection_job,
        IntervalTrigger(seconds=settings.SYNC_INTERVAL),
        id="storage_change_detection",
        name="Storage Change Detection",
        replace_existing=True,
    )
    logger.info(f"Scheduled storage change detection: every {settings.SYNC_INTERVAL}s")

    # Schedule urgency zone recalculation daily at 12:05 AM
    # This ensures tasks due today get promoted to Critical Now at the start of each day
    _scheduler.add_job(
        urgency_zone_recalculation_job,
        CronTrigger(hour=0, minute=5),
        id="urgency_zone_recalculation",
        name="Daily Urgency Zone Recalculation",
        replace_existing=True,
    )
    logger.info("Scheduled urgency zone recalculation: daily at 12:05 AM")


    # Schedule trial expiry processing daily at 3:00 AM
    # Downgrades any license whose trial_expires_at has passed and is not yet paid.
    # This is the commercial gate that makes the reverse-trial model work.
    _scheduler.add_job(
        trial_expiry_job,
        CronTrigger(hour=3, minute=0),
        id="trial_expiry",
        name="Daily Trial Expiry Processing",
        replace_existing=True,
    )
    logger.info("Scheduled trial expiry processing: daily at 3:00 AM")

    _scheduler.start()
    logger.info("Background scheduler started")


def stop_scheduler():
    """Stop the background task scheduler"""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Background scheduler stopped")


async def run_momentum_recalculation_now():
    """
    Manually trigger momentum recalculation.

    Can be called from an API endpoint for immediate updates.
    """
    await momentum_recalculation_job()


async def run_urgency_zone_recalculation_now():
    """
    Manually trigger urgency zone recalculation.

    Can be called from an API endpoint or at startup for immediate updates.
    """
    await urgency_zone_recalculation_job()
