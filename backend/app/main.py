"""
FastAPI application entry point

Supports modular architecture with commercial configurations:
- basic: Core + Projects
- gtd: Core + Projects + Inbox
- proactive_assistant: Core + Projects + Memory Layer + AI Context
- full: All modules

Set COMMERCIAL_MODE in .env or use ENABLED_MODULES for custom configs.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

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
from app.core.database import enable_wal_mode
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


# =============================================================================
# Module System Initialization
# =============================================================================

def run_migrations():
    """Run Alembic migrations on startup (idempotent — no-ops if already current)."""
    try:
        from alembic.config import Config
        from alembic import command
        from app.core.paths import get_alembic_ini_path, get_alembic_dir

        alembic_cfg = Config(str(get_alembic_ini_path()))
        alembic_cfg.set_main_option(
            "script_location", str(get_alembic_dir())
        )
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations: up to date")
    except Exception as e:
        logger.warning(f"Alembic migration skipped: {e} (falling back to create_all)")


def register_modules():
    """Register all available modules with the module registry"""
    from app.modules.registry import register_all_modules, set_enabled_modules

    # Register all modules
    register_all_modules()

    # Set enabled modules from config
    enabled = set(settings.get_enabled_modules())
    set_enabled_modules(enabled)

    return enabled


def mount_module_routers(app: FastAPI, enabled_modules: set[str]):
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
# Lifespan (startup + shutdown)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup logic before yield, shutdown after."""
    # --- Startup ---
    # Ensure database directory exists
    db_dir = Path(settings.DATABASE_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    # Run Alembic migrations first (creates/updates schema)
    run_migrations()

    # Fallback: create_all for any tables not covered by migrations
    from app.core.database import init_db
    init_db()

    enable_wal_mode()

    enabled_modules = register_modules()

    logger.info(f"{settings.APP_NAME} v{settings.VERSION} started")
    logger.info(f"Commercial mode: {settings.COMMERCIAL_MODE}")
    logger.info(f"Enabled modules: {', '.join(sorted(enabled_modules))}")
    logger.info(f"Database: {settings.DATABASE_PATH}")
    logger.info(f"Synced notes folder: {settings.SECOND_BRAIN_ROOT}")
    logger.info(f"Authentication: {'Enabled' if settings.AUTH_ENABLED else 'Disabled'}")
    if settings.LOG_TO_FILE:
        logger.info(f"Log file: {get_log_file_path()}")

    from app.modules.registry import registry
    app_context = {
        "app": app,
        "settings": settings,
    }
    await registry.initialize_all(enabled_modules, app_context)

    mount_module_routers(app, enabled_modules)

    from app.services.scheduler_service import start_scheduler
    start_scheduler()

    from app.services.scheduler_service import run_urgency_zone_recalculation_now
    await run_urgency_zone_recalculation_now()

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

    yield

    # --- Shutdown ---
    from app.modules.registry import registry as reg
    await reg.shutdown_all()

    from app.services.scheduler_service import stop_scheduler
    try:
        stop_scheduler()
    except Exception as e:
        logger.debug(f"Scheduler cleanup: {e}")

    from app.sync.file_watcher import stop_file_watcher
    try:
        stop_file_watcher()
    except Exception as e:
        logger.debug(f"File watcher cleanup: {e}")

    from app.sync.folder_watcher import stop_folder_watcher
    try:
        stop_folder_watcher()
    except Exception as e:
        logger.debug(f"Folder watcher cleanup: {e}")


# =============================================================================
# Create FastAPI Application
# =============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Intelligent momentum system for independent operators, with markdown file sync. "
                f"Commercial mode: {settings.COMMERCIAL_MODE}",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
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
    """Root endpoint — serves SPA if frontend build exists, otherwise API info."""
    from app.core.paths import get_frontend_dist
    # In production (frontend build present), serve the SPA
    _dist = get_frontend_dist() / "index.html"
    if _dist.is_file():
        return FileResponse(str(_dist))

    # In development (no build), return API info
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


@app.get("/api/v1/legal/eula")
async def get_eula():
    """Return the EULA/LICENSE text for display in the app."""
    from app.core.paths import is_packaged

    # In packaged mode: LICENSE is in the install directory (next to the exe)
    if is_packaged():
        # The exe is in the install dir; LICENSE is alongside it
        exe_dir = Path(sys.executable).parent
        license_path = exe_dir / "LICENSE"
    else:
        # Development: project root
        license_path = Path(__file__).resolve().parent.parent.parent / "LICENSE"

    if license_path.is_file():
        return PlainTextResponse(license_path.read_text(encoding="utf-8"))

    return PlainTextResponse("License file not found.", status_code=404)


@app.get("/api/v1/legal/third-party")
async def get_third_party_licenses():
    """Return third-party license notices."""
    from app.core.paths import is_packaged

    if is_packaged():
        exe_dir = Path(sys.executable).parent
        tp_path = exe_dir / "THIRD_PARTY_LICENSES.txt"
    else:
        tp_path = Path(__file__).resolve().parent.parent.parent / "THIRD_PARTY_LICENSES.txt"

    if tp_path.is_file():
        return PlainTextResponse(tp_path.read_text(encoding="utf-8"))

    return PlainTextResponse("Third-party licenses file not found.", status_code=404)


@app.post("/api/v1/shutdown")
async def request_shutdown(request: Request):
    """Request graceful server shutdown.

    Only accepts requests from localhost for security.
    Used by the installer and system tray for clean shutdown
    instead of force-killing the process.
    """
    from fastapi.responses import JSONResponse

    # Security: only allow from localhost
    client_host = request.client.host if request.client else None
    if client_host not in ("127.0.0.1", "::1", "localhost"):
        return JSONResponse(
            {"detail": "Shutdown can only be requested from localhost"},
            status_code=403,
        )

    from app.core.shutdown import shutdown_event

    logger.info("Graceful shutdown requested via API")
    shutdown_event.set()

    return {"message": "Shutdown initiated", "status": "shutting_down"}


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

# Inbox module (always mounted, but could be gated in future)
app.include_router(inbox.router, prefix=f"{settings.API_V1_PREFIX}/inbox", tags=["Inbox"])

# Data Export (BACKLOG-074: Data portability)
app.include_router(export.router, prefix=f"{settings.API_V1_PREFIX}/export", tags=["Export"])

# Settings (AI config, momentum thresholds)
app.include_router(
    settings_api.router, prefix=f"{settings.API_V1_PREFIX}/settings", tags=["Settings"]
)

# Setup wizard (first-run configuration)
from app.api import setup as setup_api
app.include_router(
    setup_api.router, prefix=f"{settings.API_V1_PREFIX}/setup", tags=["Setup"]
)


# =============================================================================
# Static File Serving (Production: serve React build from FastAPI)
# =============================================================================

# Serve frontend build if it exists (eliminates Node.js requirement for end users)
from app.core.paths import get_frontend_dist
_frontend_dist = get_frontend_dist()
if _frontend_dist.is_dir():
    # Serve static assets (JS, CSS, images)
    app.mount(
        "/assets",
        StaticFiles(directory=str(_frontend_dist / "assets")),
        name="static-assets",
    )

    # Catch-all: serve index.html for client-side routing (SPA)
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the React SPA for any unmatched routes."""
        # Don't serve SPA for API routes (they should 404 naturally)
        if full_path.startswith("api/") or full_path.startswith("modules") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("health") or full_path.startswith("openapi.json"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)

        # Serve specific static files (favicon, manifest, etc.)
        file_path = _frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))

        # Default: serve index.html for client-side routing
        index_path = _frontend_dist / "index.html"
        if index_path.is_file():
            return FileResponse(str(index_path))

        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Not Found"}, status_code=404)


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
