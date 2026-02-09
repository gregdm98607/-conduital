@echo off
echo ========================================
echo Conduital - Development Servers
echo ========================================
echo.

REM Check if backend directory exists
if not exist "backend" (
    echo ERROR: backend directory not found
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "frontend" (
    echo ERROR: frontend directory not found
    pause
    exit /b 1
)

REM Check .env configuration
echo Checking configuration...
if exist "backend\.env" (
    echo ✓ Found .env configuration
    findstr /C:"AUTO_DISCOVERY_ENABLED=true" backend\.env >nul
    if %errorlevel% equ 0 (
        echo ✓ Auto-discovery: ENABLED
        echo   ^(New project folders will import automatically^)
    ) else (
        echo ℹ Auto-discovery: Disabled
        echo   ^(Enable in backend\.env to auto-import new projects^)
    )
) else (
    echo ⚠ No .env file found - using defaults
)
echo.

echo Starting Backend Server...
if exist "backend\venv\Scripts\activate.bat" (
    echo Using virtual environment...
    start "Backend Server" cmd /k "cd backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
) else (
    echo Checking for Poetry...
    where poetry >nul 2>&1
    if %errorlevel% equ 0 (
        echo Using Poetry...
        start "Backend Server" cmd /k "cd backend && poetry run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    ) else (
        echo WARNING: No Poetry or venv found. Using system Python...
        echo          This may cause issues if Pydantic V2 is not installed globally.
        start "Backend Server" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    )
)

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo  Development Servers Running
echo ========================================
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo ========================================
echo.
echo Features:
echo - Phase 1: Manual project discovery
echo - Phase 2: Auto-discovery ^(if enabled^)
echo - AI features ^(if API key configured^)
echo - Momentum tracking
echo - Bidirectional sync
echo.
echo Useful Commands:
echo - Create markdown files: poetry run python scripts/create_project_files.py
echo - Run discovery:        poetry run python scripts/discover_projects.py
echo - Update momentum:      curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update
echo.
echo Press any key to exit ^(servers will keep running^)
pause >nul
