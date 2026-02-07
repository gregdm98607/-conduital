"""
FastAPI application entry point

Supports modular architecture with commercial configurations:
- basic: Core + Projects
- gtd: Core + Projects + GTD Inbox
- proactive_assistant: Core + Projects + Memory Layer + AI Context
- full: All modules

Set COMMERCIAL_MODE in .env or use ENABLED_MODULES for custom configs.
"""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core API routers (always loaded for backwards compatibility)
from app.api import (
    auth,
    projects,
    tasks,
    next_actions,
    areas,
    goals,
    visions,
    contexts,
    inbox,
    sync,
    intelligence,
    discovery,
    export,
    settings as settings_api,
)
from app.core.config import settings
from app.core.database import enable_wal_mode, get_db
from app.core.logging_config import setup_logging, get_log_file_path

# Initialize logging before anything else
setup_logging(
    log_dir=Path(settings.LOG_DIR) if settings.LOG_DIR else None,
    log_level=settings.LOG_LEVEL,
    log_to_console=settings.LOG_TO_CONSOLE,
    log_to_file=settings.LOG_TO_FILE,
    max_bytes=settings.LOG_MAX_BYTES,
    backup_count=settings.LOG_BACKUP_COUNT,
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="GTD + Manage Your Now project management system with Second Brain integration. "
                f"Commercial mode: {settings.COMMERCIAL_MODE}",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Module System Initialization
# =============================================================================

def register_modules():
    """Register all available modules with the module registry"""
    from app.modules.registry import register_all_modules, set_enabled_modules

    # Register all modules
    register_all_modules()

    # Set enabled modules from config
    enabled = set(settings.get_enabled_modules())
    set_enabled_modules(enabled)

    return enabled


def mount_module_routers(enabled_modules: set[str]):
    """Mount routers for enabled modules"""
    from app.modules.registry import registry

    for module_name in enabled_modules:
        module = registry.get(module_name)
        if module and module.router and module.prefix:
            prefix = f"{settings.API_V1_PREFIX}/{module.prefix}"
            app.include_router(
                module.router,
                prefix=prefix,
                tags=module.tags,
            )
            logger.debug(f"Mounted module router: {module_name} at {prefix}")


# =============================================================================
# Startup Event
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Initialize database tables if they don't exist
    from app.core.database import init_db
    init_db()

    # Enable WAL mode for better concurrency
    enable_wal_mode()

    # Register and initialize modules
    enabled_modules = register_modules()

    logger.info(f"{settings.APP_NAME} v{settings.VERSION} started")
    logger.info(f"Commercial mode: {settings.COMMERCIAL_MODE}")
    logger.info(f"Enabled modules: {', '.join(sorted(enabled_modules))}")
    logger.info(f"Database: {settings.DATABASE_PATH}")
    logger.info(f"Second Brain: {settings.SECOND_BRAIN_ROOT}")
    logger.info(f"Authentication: {'Enabled' if settings.AUTH_ENABLED else 'Disabled'}")
    if settings.LOG_TO_FILE:
        logger.info(f"Log file: {get_log_file_path()}")

    # Initialize modules (async initialization)
    from app.modules.registry import registry
    app_context = {
        "app": app,
        "settings": settings,
    }
    await registry.initialize_all(enabled_modules, app_context)

    # Mount module-specific routers
    mount_module_routers(enabled_modules)

    # Start background scheduler for periodic tasks
    from app.services.scheduler_service import start_scheduler
    start_scheduler()

    # Recalculate urgency zones on startup so tasks due today are promoted to Critical Now
    from app.services.scheduler_service import run_urgency_zone_recalculation_now
    await run_urgency_zone_recalculation_now()

    # Legacy: Start folder watcher for auto-discovery if enabled
    # (This will be moved to projects module in future)
    if settings.AUTO_DISCOVERY_ENABLED and "projects" in enabled_modules and settings.SECOND_BRAIN_ROOT:
        from app.sync.folder_watcher import start_folder_watcher
        from app.services.auto_discovery_service import (
            on_new_folder_created,
            on_folder_renamed,
            on_folder_moved,
            on_area_created,
            on_area_renamed,
            on_area_moved,
        )
        start_folder_watcher(
            on_folder_created=on_new_folder_created,
            on_folder_renamed=on_folder_renamed,
            on_folder_moved=on_folder_moved,
            on_area_created=on_area_created,
            on_area_renamed=on_area_renamed,
            on_area_moved=on_area_moved,
        )
        logger.info("Auto-discovery enabled (Projects & Areas)")


# =============================================================================
# Shutdown Event
# =============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Shutdown all modules
    from app.modules.registry import registry
    await registry.shutdown_all()

    # Stop background scheduler
    from app.services.scheduler_service import stop_scheduler
    try:
        stop_scheduler()
    except Exception as e:
        logger.debug(f"Scheduler cleanup: {e}")

    # Stop file watcher if running
    from app.sync.file_watcher import stop_file_watcher
    try:
        stop_file_watcher()
    except Exception as e:
        logger.debug(f"File watcher cleanup: {e}")

    # Stop folder watcher if running
    from app.sync.folder_watcher import stop_folder_watcher
    try:
        stop_folder_watcher()
    except Exception as e:
        logger.debug(f"Folder watcher cleanup: {e}")


# =============================================================================
# Health & Info Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "commercial_mode": settings.COMMERCIAL_MODE,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "commercial_mode": settings.COMMERCIAL_MODE,
        "enabled_modules": settings.get_enabled_modules(),
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/modules")
async def list_modules():
    """List all available and enabled modules"""
    from app.modules.registry import registry, get_enabled_module_names

    enabled = get_enabled_module_names()
    all_modules = registry.all()

    return {
        "commercial_mode": settings.COMMERCIAL_MODE,
        "enabled_modules": list(enabled),
        "available_modules": [
            {
                "name": m.info.name,
                "display_name": m.info.display_name,
                "description": m.info.description,
                "category": m.info.category.value,
                "enabled": m.info.name in enabled,
                "dependencies": m.info.dependencies,
            }
            for m in all_modules
        ],
    }


# =============================================================================
# Core API Routers (always mounted for backwards compatibility)
# =============================================================================

# These routers are always available regardless of module configuration
# to maintain backwards compatibility with existing clients

# Authentication (gated by AUTH_ENABLED setting)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Authentication"])

# Core: Areas, Contexts, Goals, Visions
app.include_router(areas.router, prefix=f"{settings.API_V1_PREFIX}/areas", tags=["Areas"])
app.include_router(contexts.router, prefix=f"{settings.API_V1_PREFIX}/contexts", tags=["Contexts"])
app.include_router(goals.router, prefix=f"{settings.API_V1_PREFIX}/goals", tags=["Goals"])
app.include_router(visions.router, prefix=f"{settings.API_V1_PREFIX}/visions", tags=["Visions"])

# Projects: Projects, Tasks, Next Actions, Sync, Discovery, Intelligence
app.include_router(projects.router, prefix=f"{settings.API_V1_PREFIX}/projects", tags=["Projects"])
app.include_router(tasks.router, prefix=f"{settings.API_V1_PREFIX}/tasks", tags=["Tasks"])
app.include_router(
    next_actions.router, prefix=f"{settings.API_V1_PREFIX}/next-actions", tags=["Next Actions"]
)
app.include_router(sync.router, prefix=f"{settings.API_V1_PREFIX}/sync", tags=["Sync"])
app.include_router(
    intelligence.router, prefix=f"{settings.API_V1_PREFIX}/intelligence", tags=["Intelligence"]
)
app.include_router(
    discovery.router, prefix=f"{settings.API_V1_PREFIX}/discovery", tags=["Discovery"]
)

# GTD Inbox (always mounted, but could be gated in future)
app.include_router(inbox.router, prefix=f"{settings.API_V1_PREFIX}/inbox", tags=["Inbox"])

# Data Export (BACKLOG-074: Data portability)
app.include_router(export.router, prefix=f"{settings.API_V1_PREFIX}/export", tags=["Export"])

# Settings (AI config, momentum thresholds)
app.include_router(
    settings_api.router, prefix=f"{settings.API_V1_PREFIX}/settings", tags=["Settings"]
)


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
    )
