"""
Seed sample data for testing Conduital.

Run from backend directory:
    python -m scripts.seed_sample_data
"""

import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine
from app.models import (
    Area,
    Base,
    Goal,
    InboxItem,
    MomentumSnapshot,
    Project,
    Task,
    Vision,
    WeeklyReviewCompletion,
)

now = datetime.now(timezone.utc)

# Short aliases for readability in lookups
AREA = {
    "dev": "Software Development",
    "writing": "Writing & Content",
    "health": "Health & Fitness",
    "finance": "Finance",
    "family": "Relationships & Family",
    "home": "Home & Environment",
}
GOAL = {
    "conduital": "Launch Conduital v1.0 publicly",
    "writing": "Build a writing habit — publish 50 articles",
    "marathon": "Complete a half marathon",
    "savings": "Save 6-month emergency fund",
}
VISION = {
    "ai_expert": "Become a recognized expert in AI-augmented productivity",
    "financial": "Financial independence through product income",
    "health": "Live a healthy, balanced life with strong relationships",
}
PROJ = {
    "conduital": "Conduital v1.0 Release",
    "cli": "Open Source CLI Tool — taskmd",
    "astro": "Migrate personal site to Astro",
    "blog": "Blog Series: AI-Augmented GTD",
    "book": "Productivity Book Outline",
    "marathon": "Half Marathon Training Plan",
    "meditation": "Build a Meditation Habit",
    "tax": "2026 Tax Preparation",
    "index_fund": "Research Index Fund Portfolio",
    "reunion": "Plan Summer Family Reunion",
    "declutter": "Spring Declutter & Organize",
    "office": "Set Up Home Office",
}


def seed_visions(db: Session) -> dict[str, int]:
    """Create sample visions (3-5 year / life purpose)."""
    visions = [
        Vision(
            title=VISION["ai_expert"],
            description=(
                "Build thought leadership around how AI tools can enhance personal "
                "productivity without replacing human judgment. Publish a book, speak "
                "at conferences, and maintain an active community."
            ),
            timeframe="5_year",
        ),
        Vision(
            title=VISION["financial"],
            description=(
                "Generate enough passive and product-based income to cover living "
                "expenses, enabling full creative freedom and the ability to work "
                "on projects purely for impact."
            ),
            timeframe="5_year",
        ),
        Vision(
            title=VISION["health"],
            description=(
                "Maintain physical fitness, mental clarity, and deep connections "
                "with family and friends. Be present, not just productive."
            ),
            timeframe="life_purpose",
        ),
    ]
    db.add_all(visions)
    db.flush()
    return {v.title: v.id for v in visions}


def seed_goals(db: Session) -> dict[str, int]:
    """Create sample goals (1-3 year objectives)."""
    goals = [
        Goal(
            title=GOAL["conduital"],
            description=(
                "Ship the first public release of Conduital with core GTD features, "
                "file sync, and AI-assisted weekly reviews. Target 100 beta users."
            ),
            timeframe="1_year",
            target_date=date(2027, 1, 15),
            status="active",
        ),
        Goal(
            title=GOAL["writing"],
            description=(
                "Write and publish 50 articles on productivity, software, and AI. "
                "Establish a consistent cadence of 1 article per week."
            ),
            timeframe="2_year",
            target_date=date(2028, 2, 1),
            status="active",
        ),
        Goal(
            title=GOAL["marathon"],
            description="Train consistently and complete a half marathon under 2 hours.",
            timeframe="1_year",
            target_date=date(2026, 10, 15),
            status="active",
        ),
        Goal(
            title=GOAL["savings"],
            description=(
                "Build up savings to cover 6 months of expenses. Automate "
                "contributions and reduce discretionary spending."
            ),
            timeframe="1_year",
            target_date=date(2027, 6, 1),
            status="active",
        ),
    ]
    db.add_all(goals)
    db.flush()
    return {g.title: g.id for g in goals}


def seed_areas(db: Session) -> dict[str, int]:
    """Create sample areas of responsibility."""
    areas = [
        Area(
            title=AREA["dev"],
            description="All coding projects, open-source contributions, and technical skill development.",
            standard_of_excellence=(
                "Ship high-quality code with tests. Keep dependencies up to date. "
                "Review and refactor regularly. No stale branches."
            ),
            review_frequency="weekly",
        ),
        Area(
            title=AREA["writing"],
            description="Blog posts, articles, documentation, and book projects.",
            standard_of_excellence=(
                "Publish at least one piece per week. Maintain an editorial calendar. "
                "Respond to reader feedback within 48 hours."
            ),
            review_frequency="weekly",
        ),
        Area(
            title=AREA["health"],
            description="Exercise, nutrition, sleep, and mental health practices.",
            standard_of_excellence=(
                "Exercise 4x/week. Sleep 7-8 hours. Meal prep on Sundays. "
                "Annual physical done. Mental health check-ins monthly."
            ),
            review_frequency="weekly",
        ),
        Area(
            title=AREA["finance"],
            description="Budgeting, investments, taxes, and financial planning.",
            standard_of_excellence=(
                "Budget reviewed monthly. Investments rebalanced quarterly. "
                "Tax prep started by February. No surprise expenses."
            ),
            review_frequency="monthly",
        ),
        Area(
            title=AREA["family"],
            description="Maintaining connections with family, friends, and community.",
            standard_of_excellence=(
                "Weekly family dinner. Monthly catch-up with close friends. "
                "Remember birthdays. Be fully present during quality time."
            ),
            review_frequency="weekly",
        ),
        Area(
            title=AREA["home"],
            description="Home maintenance, organization, and living space quality.",
            standard_of_excellence=(
                "Declutter quarterly. Handle repairs within a week. "
                "Keep workspace clean and inspiring."
            ),
            review_frequency="monthly",
        ),
    ]
    db.add_all(areas)
    db.flush()
    return {a.title: a.id for a in areas}


def seed_projects(
    db: Session,
    area_ids: dict[str, int],
    goal_ids: dict[str, int],
    vision_ids: dict[str, int],
) -> dict[str, int]:
    """Create sample projects across areas."""
    projects = [
        # --- Software Development ---
        Project(
            title=PROJ["conduital"],
            description="Ship the first public release with all core features.",
            outcome_statement="Conduital is live on the web with 100+ beta signups.",
            status="active",
            priority=2,
            momentum_score=0.72,
            previous_momentum_score=0.65,
            area_id=area_ids[AREA["dev"]],
            goal_id=goal_ids[GOAL["conduital"]],
            purpose="Create a productivity tool that actually respects how people think.",
            vision_statement="A seamless GTD system that syncs with markdown files and uses AI wisely.",
            brainstorm_notes="File sync, momentum scoring, weekly review, inbox capture, AI summaries",
            organizing_notes="Phase 1: Core CRUD. Phase 2: File sync. Phase 3: AI features. Phase 4: Polish.",
            review_frequency="weekly",
            last_activity_at=now - timedelta(hours=3),
            target_completion_date=date(2026, 6, 1),
        ),
        Project(
            title=PROJ["cli"],
            description="A CLI tool for managing tasks in markdown files. Complements Conduital.",
            outcome_statement="Published on PyPI with 50+ GitHub stars.",
            status="active",
            priority=5,
            momentum_score=0.35,
            previous_momentum_score=0.50,
            area_id=area_ids[AREA["dev"]],
            purpose="Give power users a terminal-native way to manage GTD tasks.",
            review_frequency="weekly",
            last_activity_at=now - timedelta(days=10),
            target_completion_date=date(2026, 9, 1),
        ),
        Project(
            title=PROJ["astro"],
            description="Rewrite personal website from Next.js to Astro for better performance.",
            outcome_statement="Site is live on Astro with <1s load times and all content migrated.",
            status="someday_maybe",
            priority=7,
            momentum_score=0.0,
            area_id=area_ids[AREA["dev"]],
            review_frequency="monthly",
        ),
        # --- Writing & Content ---
        Project(
            title=PROJ["blog"],
            description="A 5-part blog series exploring how AI can enhance the GTD methodology.",
            outcome_statement="All 5 posts published, with at least 1000 total reads.",
            status="active",
            priority=3,
            momentum_score=0.55,
            previous_momentum_score=0.40,
            area_id=area_ids[AREA["writing"]],
            goal_id=goal_ids[GOAL["writing"]],
            review_frequency="weekly",
            last_activity_at=now - timedelta(days=2),
            target_completion_date=date(2026, 4, 30),
        ),
        Project(
            title=PROJ["book"],
            description="Draft a detailed outline for a book on momentum-based productivity.",
            outcome_statement="Complete outline with chapter summaries shared with 3 beta readers.",
            status="on_hold",
            priority=4,
            momentum_score=0.15,
            previous_momentum_score=0.30,
            area_id=area_ids[AREA["writing"]],
            goal_id=goal_ids[GOAL["writing"]],
            vision_id=vision_ids[VISION["ai_expert"]],
            review_frequency="monthly",
            last_activity_at=now - timedelta(days=30),
        ),
        # --- Health & Fitness ---
        Project(
            title=PROJ["marathon"],
            description="Follow a 16-week training plan for the autumn half marathon.",
            outcome_statement="Complete the half marathon in under 2 hours.",
            status="active",
            priority=3,
            momentum_score=0.80,
            previous_momentum_score=0.75,
            area_id=area_ids[AREA["health"]],
            goal_id=goal_ids[GOAL["marathon"]],
            review_frequency="weekly",
            last_activity_at=now - timedelta(days=1),
            target_completion_date=date(2026, 10, 15),
        ),
        Project(
            title=PROJ["meditation"],
            description="Establish a daily 10-minute meditation practice.",
            outcome_statement="30 consecutive days of meditation completed.",
            status="active",
            priority=5,
            momentum_score=0.45,
            previous_momentum_score=0.20,
            area_id=area_ids[AREA["health"]],
            review_frequency="weekly",
            last_activity_at=now - timedelta(days=3),
        ),
        # --- Finance ---
        Project(
            title=PROJ["tax"],
            description="Gather documents, organize receipts, and file 2025 taxes.",
            outcome_statement="Taxes filed accurately before the April deadline.",
            status="active",
            priority=2,
            momentum_score=0.60,
            previous_momentum_score=0.45,
            area_id=area_ids[AREA["finance"]],
            review_frequency="weekly",
            last_activity_at=now - timedelta(days=4),
            target_completion_date=date(2026, 4, 15),
        ),
        Project(
            title=PROJ["index_fund"],
            description="Compare low-cost index fund options and set up automated investing.",
            outcome_statement="Automated monthly investment into a diversified 3-fund portfolio.",
            status="active",
            priority=4,
            momentum_score=0.25,
            previous_momentum_score=0.25,
            area_id=area_ids[AREA["finance"]],
            goal_id=goal_ids[GOAL["savings"]],
            review_frequency="monthly",
            last_activity_at=now - timedelta(days=14),
        ),
        # --- Relationships ---
        Project(
            title=PROJ["reunion"],
            description="Organize a family gathering for July — venue, food, activities.",
            outcome_statement="20+ family members attend a fun, stress-free weekend event.",
            status="active",
            priority=4,
            momentum_score=0.30,
            previous_momentum_score=0.10,
            area_id=area_ids[AREA["family"]],
            review_frequency="weekly",
            last_activity_at=now - timedelta(days=7),
            target_completion_date=date(2026, 7, 15),
        ),
        # --- Home ---
        Project(
            title=PROJ["declutter"],
            description="Go room by room to declutter, donate, and reorganize.",
            outcome_statement="Every room decluttered with donation boxes dropped off.",
            status="someday_maybe",
            priority=6,
            momentum_score=0.0,
            area_id=area_ids[AREA["home"]],
            review_frequency="monthly",
        ),
        Project(
            title=PROJ["office"],
            description="Ergonomic desk, monitor, good lighting, cable management.",
            outcome_statement="Comfortable, productive home office setup.",
            status="completed",
            priority=5,
            momentum_score=1.0,
            area_id=area_ids[AREA["home"]],
            completed_at=now - timedelta(days=45),
            last_activity_at=now - timedelta(days=45),
        ),
    ]
    db.add_all(projects)
    db.flush()
    return {p.title: p.id for p in projects}


def seed_tasks(db: Session, pid: dict[str, int]) -> None:
    """Create sample tasks across projects."""
    tasks = [
        # --- Conduital v1.0 ---
        Task(
            title="Fix weekly review page loading spinner",
            project_id=pid[PROJ["conduital"]],
            status="in_progress",
            task_type="action",
            priority=2,
            is_next_action=True,
            context="computer",
            energy_level="high",
            urgency_zone="critical_now",
            estimated_minutes=30,
        ),
        Task(
            title="Add collapsible sections to ProjectDetail page",
            project_id=pid[PROJ["conduital"]],
            status="pending",
            task_type="action",
            priority=3,
            is_next_action=True,
            context="computer",
            energy_level="medium",
            urgency_zone="opportunity_now",
            estimated_minutes=90,
        ),
        Task(
            title="Write API docs for file sync endpoints",
            project_id=pid[PROJ["conduital"]],
            status="pending",
            task_type="action",
            priority=5,
            context="computer",
            energy_level="medium",
            urgency_zone="over_the_horizon",
            estimated_minutes=120,
        ),
        Task(
            title="Set up CI/CD pipeline with GitHub Actions",
            project_id=pid[PROJ["conduital"]],
            status="completed",
            task_type="action",
            priority=2,
            context="computer",
            completed_at=now - timedelta(days=5),
            actual_minutes=180,
        ),
        Task(
            title="Get feedback from 3 beta testers",
            project_id=pid[PROJ["conduital"]],
            status="waiting",
            task_type="waiting_for",
            priority=3,
            waiting_for="Beta testers (Alex, Sam, Jordan)",
            urgency_zone="opportunity_now",
        ),
        Task(
            title="Design landing page mockup",
            project_id=pid[PROJ["conduital"]],
            status="pending",
            task_type="action",
            priority=4,
            context="computer",
            energy_level="high",
            urgency_zone="over_the_horizon",
            estimated_minutes=240,
            defer_until=date(2026, 4, 1),
        ),
        # --- CLI Tool ---
        Task(
            title="Define CLI argument structure with Click",
            project_id=pid[PROJ["cli"]],
            status="pending",
            task_type="action",
            priority=3,
            is_next_action=True,
            context="computer",
            energy_level="high",
            urgency_zone="opportunity_now",
            estimated_minutes=60,
        ),
        Task(
            title="Write README with usage examples",
            project_id=pid[PROJ["cli"]],
            status="pending",
            task_type="action",
            priority=5,
            context="computer",
            energy_level="low",
            urgency_zone="over_the_horizon",
            estimated_minutes=45,
        ),
        # --- Blog Series ---
        Task(
            title="Draft Part 3: AI-Powered Weekly Reviews",
            project_id=pid[PROJ["blog"]],
            status="in_progress",
            task_type="action",
            priority=3,
            is_next_action=True,
            context="computer",
            energy_level="high",
            urgency_zone="opportunity_now",
            estimated_minutes=120,
        ),
        Task(
            title="Edit and publish Part 2: Momentum Scoring",
            project_id=pid[PROJ["blog"]],
            status="pending",
            task_type="action",
            priority=2,
            is_next_action=True,
            context="computer",
            energy_level="medium",
            urgency_zone="critical_now",
            estimated_minutes=60,
            due_date=date(2026, 2, 25),
        ),
        Task(
            title="Research existing AI-GTD tools for Part 1 references",
            project_id=pid[PROJ["blog"]],
            status="completed",
            task_type="action",
            priority=4,
            completed_at=now - timedelta(days=8),
            actual_minutes=90,
        ),
        # --- Book Outline ---
        Task(
            title="Read 'Getting Things Done' for fresh notes",
            project_id=pid[PROJ["book"]],
            status="pending",
            task_type="action",
            priority=5,
            context="reading",
            energy_level="medium",
            urgency_zone="over_the_horizon",
            estimated_minutes=300,
        ),
        # --- Half Marathon ---
        Task(
            title="Complete Week 6 training runs (3x)",
            project_id=pid[PROJ["marathon"]],
            status="in_progress",
            task_type="action",
            priority=2,
            is_next_action=True,
            energy_level="high",
            urgency_zone="critical_now",
            due_date=date(2026, 2, 23),
        ),
        Task(
            title="Buy new running shoes",
            project_id=pid[PROJ["marathon"]],
            status="pending",
            task_type="action",
            priority=4,
            context="errands",
            energy_level="low",
            urgency_zone="opportunity_now",
            estimated_minutes=60,
        ),
        Task(
            title="Register for the October race",
            project_id=pid[PROJ["marathon"]],
            status="completed",
            task_type="milestone",
            priority=1,
            completed_at=now - timedelta(days=20),
        ),
        # --- Meditation ---
        Task(
            title="Download Insight Timer app",
            project_id=pid[PROJ["meditation"]],
            status="completed",
            task_type="action",
            priority=3,
            is_two_minute_task=True,
            completed_at=now - timedelta(days=10),
            actual_minutes=2,
        ),
        Task(
            title="Meditate for 10 minutes before work",
            project_id=pid[PROJ["meditation"]],
            status="pending",
            task_type="action",
            priority=3,
            is_next_action=True,
            energy_level="low",
            urgency_zone="opportunity_now",
        ),
        # --- Tax Prep ---
        Task(
            title="Gather W-2 and 1099 forms",
            project_id=pid[PROJ["tax"]],
            status="completed",
            task_type="action",
            priority=1,
            context="home",
            completed_at=now - timedelta(days=7),
        ),
        Task(
            title="Organize charitable donation receipts",
            project_id=pid[PROJ["tax"]],
            status="in_progress",
            task_type="action",
            priority=3,
            is_next_action=True,
            context="home",
            energy_level="low",
            urgency_zone="opportunity_now",
            estimated_minutes=45,
        ),
        Task(
            title="Schedule appointment with tax preparer",
            project_id=pid[PROJ["tax"]],
            status="pending",
            task_type="action",
            priority=2,
            is_two_minute_task=True,
            context="phone",
            urgency_zone="critical_now",
            due_date=date(2026, 3, 1),
        ),
        # --- Index Fund ---
        Task(
            title="Compare Vanguard vs Fidelity expense ratios",
            project_id=pid[PROJ["index_fund"]],
            status="pending",
            task_type="action",
            priority=4,
            is_next_action=True,
            context="computer",
            energy_level="medium",
            urgency_zone="opportunity_now",
            estimated_minutes=60,
        ),
        Task(
            title="Read Bogleheads 3-fund portfolio guide",
            project_id=pid[PROJ["index_fund"]],
            status="pending",
            task_type="action",
            priority=5,
            context="reading",
            energy_level="medium",
            urgency_zone="over_the_horizon",
            estimated_minutes=90,
        ),
        # --- Family Reunion ---
        Task(
            title="Research venue options (park vs. rental hall)",
            project_id=pid[PROJ["reunion"]],
            status="pending",
            task_type="action",
            priority=3,
            is_next_action=True,
            context="computer",
            energy_level="medium",
            urgency_zone="opportunity_now",
            estimated_minutes=60,
        ),
        Task(
            title="Create shared Google Doc for menu planning",
            project_id=pid[PROJ["reunion"]],
            status="pending",
            task_type="action",
            priority=5,
            is_two_minute_task=True,
            context="computer",
            energy_level="low",
            urgency_zone="over_the_horizon",
            estimated_minutes=5,
        ),
        Task(
            title="Send save-the-date to family group chat",
            project_id=pid[PROJ["reunion"]],
            status="pending",
            task_type="action",
            priority=4,
            context="phone",
            energy_level="low",
            urgency_zone="opportunity_now",
            estimated_minutes=5,
        ),
    ]
    db.add_all(tasks)
    db.flush()


def seed_inbox(db: Session) -> None:
    """Create sample inbox items (mix of processed and unprocessed)."""
    items = [
        InboxItem(
            content="Look into Obsidian plugin for Conduital sync",
            source="web_ui",
        ),
        InboxItem(
            content="Interesting article on spaced repetition — could apply to review frequency",
            source="web_ui",
        ),
        InboxItem(
            content="Mom's birthday is March 15 — plan something",
            source="web_ui",
        ),
        InboxItem(
            content="Check if car registration is due this month",
            source="web_ui",
        ),
        InboxItem(
            content="Idea: Add a 'focus mode' to Conduital that hides everything except current next actions",
            source="web_ui",
        ),
        InboxItem(
            content="Need to return the library books by Friday",
            source="web_ui",
        ),
        # Already-processed items
        InboxItem(
            content="Set up GitHub Actions for Conduital",
            source="web_ui",
            processed_at=now - timedelta(days=6),
            result_type="task",
        ),
        InboxItem(
            content="Random thought about nothing actionable",
            source="web_ui",
            processed_at=now - timedelta(days=3),
            result_type="trash",
        ),
    ]
    db.add_all(items)
    db.flush()


def seed_weekly_reviews(db: Session) -> None:
    """Create a couple of past weekly review completions."""
    reviews = [
        WeeklyReviewCompletion(
            completed_at=now - timedelta(days=7),
            notes="Good week. Cleared inbox, updated all project statuses. Need to focus more on the blog series.",
        ),
        WeeklyReviewCompletion(
            completed_at=now - timedelta(days=14),
            notes="Stalled on the book outline. Decided to put it on hold and focus on shipping Conduital.",
        ),
    ]
    db.add_all(reviews)
    db.flush()


def seed_momentum_snapshots(db: Session, pid: dict[str, int]) -> None:
    """Create historical momentum snapshots for sparkline charts."""
    snapshots = {
        pid[PROJ["conduital"]]: {
            "scores": [0.30, 0.35, 0.40, 0.42, 0.50, 0.55, 0.60, 0.65, 0.68, 0.72],
            "factors": '{"activity": 0.8, "completion_rate": 0.6, "next_actions": 1.0}',
        },
        pid[PROJ["marathon"]]: {
            "scores": [0.60, 0.65, 0.70, 0.72, 0.75, 0.75, 0.78, 0.78, 0.80, 0.80],
            "factors": '{"activity": 0.9, "completion_rate": 0.7, "next_actions": 0.8}',
        },
        pid[PROJ["blog"]]: {
            "scores": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55],
            "factors": '{"activity": 0.5, "completion_rate": 0.4, "next_actions": 0.7}',
        },
    }
    for project_id, data in snapshots.items():
        scores = data["scores"]
        for i, score in enumerate(scores):
            db.add(
                MomentumSnapshot(
                    project_id=project_id,
                    score=score,
                    factors_json=data["factors"],
                    snapshot_at=now - timedelta(days=(len(scores) - i)),
                )
            )
    db.flush()


def main() -> None:
    print("Seeding sample data into Conduital...")

    # Ensure tables exist
    from app.core.database import init_db
    init_db()

    db = SessionLocal()
    try:
        existing_projects = db.query(Project).count()
        if existing_projects > 0:
            print(f"Database already has {existing_projects} projects.")
            response = input("Add sample data anyway? (y/N): ").strip().lower()
            if response != "y":
                print("Aborted.")
                return

        print("  Creating visions...")
        vision_ids = seed_visions(db)

        print("  Creating goals...")
        goal_ids = seed_goals(db)

        print("  Creating areas...")
        area_ids = seed_areas(db)

        print("  Creating projects...")
        project_ids = seed_projects(db, area_ids, goal_ids, vision_ids)

        print("  Creating tasks...")
        seed_tasks(db, project_ids)

        print("  Creating inbox items...")
        seed_inbox(db)

        print("  Creating weekly review history...")
        seed_weekly_reviews(db)

        print("  Creating momentum snapshots...")
        seed_momentum_snapshots(db, project_ids)

        db.commit()

        print("\nSample data created successfully!")
        print(f"  Visions:    {len(vision_ids)}")
        print(f"  Goals:      {len(goal_ids)}")
        print(f"  Areas:      {len(area_ids)}")
        print(f"  Projects:   {len(project_ids)}")
        print(f"  Tasks:      {db.query(Task).count()}")
        print(f"  Inbox:      {db.query(InboxItem).count()}")
        print(f"  Reviews:    {db.query(WeeklyReviewCompletion).count()}")
        print(f"  Snapshots:  {db.query(MomentumSnapshot).count()}")

    except Exception as e:
        db.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
