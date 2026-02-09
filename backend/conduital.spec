# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Conduital.

Builds a single-folder distribution with:
- Uvicorn server (FastAPI backend)
- Pre-built frontend (static files)
- Alembic migrations
- System tray icon

Usage:
    pyinstaller conduital.spec --clean
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Paths relative to this spec file (backend/)
# SPECPATH is always set by PyInstaller to the directory containing the spec file
try:
    BACKEND_DIR = os.path.abspath(SPECPATH)
except NameError:
    BACKEND_DIR = os.path.abspath('.')
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
FRONTEND_DIST = os.path.join(PROJECT_ROOT, 'frontend', 'dist')
ALEMBIC_DIR = os.path.join(BACKEND_DIR, 'alembic')
ALEMBIC_INI = os.path.join(BACKEND_DIR, 'alembic.ini')
ASSETS_DIR = os.path.join(PROJECT_ROOT, 'assets')
ICON_FILE = os.path.join(ASSETS_DIR, 'conduital.ico')

# Check for required build inputs
if not os.path.isdir(FRONTEND_DIST):
    print(f"ERROR: Frontend not built. Run 'npm run build' in frontend/ first.")
    print(f"  Expected: {FRONTEND_DIST}")
    sys.exit(1)

if not os.path.isfile(ALEMBIC_INI):
    print(f"ERROR: alembic.ini not found at {ALEMBIC_INI}")
    sys.exit(1)

# Data files to bundle
datas = [
    (FRONTEND_DIST, 'frontend_dist'),
    (ALEMBIC_DIR, 'alembic'),
    (ALEMBIC_INI, '.'),
]

# Bundle assets if they exist
if os.path.isdir(ASSETS_DIR):
    datas.append((ASSETS_DIR, 'assets'))

# Hidden imports that PyInstaller can't auto-detect
hiddenimports = [
    # FastAPI + Uvicorn internals
    'uvicorn',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.loops.asyncio',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.http.httptools_impl',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.protocols.websockets.wsproto_impl',
    'uvicorn.logging',
    'uvicorn.middleware',
    'uvicorn.middleware.proxy_headers',
    'fastapi',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'fastapi.responses',
    'fastapi.staticfiles',
    'starlette',
    'starlette.responses',
    'starlette.routing',
    'starlette.middleware',

    # SQLAlchemy
    'sqlalchemy',
    'sqlalchemy.orm',
    'sqlalchemy.exc',
    'sqlalchemy.engine',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.pool',

    # Pydantic
    'pydantic',
    'pydantic.fields',
    'pydantic_settings',

    # Alembic
    'alembic',
    'alembic.config',
    'alembic.command',
    'alembic.script',
    'alembic.runtime',
    'alembic.runtime.migration',

    # Application dependencies
    'frontmatter',
    'yaml',
    'watchdog',
    'watchdog.events',
    'watchdog.observers',
    'apscheduler',
    'apscheduler.schedulers.asyncio',
    'apscheduler.triggers.cron',
    'apscheduler.triggers.interval',
    'anthropic',
    'jose',
    'jose.jwt',
    'httpx',
    'aiofiles',
    'dotenv',
    'multipart',

    # System tray
    'pystray',
    'pystray._win32',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',

    # CLI tools (used by migration integrity check)
    'typer',
    'rich',
    'rich.console',
    'rich.panel',
    'rich.table',

    # App modules
    'app',
    'app.main',
    'app.core',
    'app.core.config',
    'app.core.paths',
    'app.core.database',
    'app.core.logging_config',
    'app.api',
    'app.models',
    'app.services',
    'app.modules',
    'app.sync',
    'app.tray',
]

# Packages to exclude (dev-only, not needed at runtime)
excludes = [
    'pytest',
    'pytest_asyncio',
    'pytest_cov',
    'black',
    'ruff',
    'mypy',
    'IPython',
    'jupyter',
    'notebook',
    'sphinx',
    'setuptools',
    'pip',
    'wheel',
    'tkinter',
    '_tkinter',
]

a = Analysis(
    [os.path.join(BACKEND_DIR, 'run.py')],
    pathex=[BACKEND_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Check for version info file
version_file = os.path.join(BACKEND_DIR, 'version_info.txt')
version_info = version_file if os.path.isfile(version_file) else None

# Check for icon file
icon = ICON_FILE if os.path.isfile(ICON_FILE) else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Conduital',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window in packaged mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=version_info,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Conduital',
)
