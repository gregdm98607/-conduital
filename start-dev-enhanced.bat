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
if not exist "backend\.env" (
    echo [!] No .env file found - using defaults
    goto :config_done
)

echo [+] Found .env configuration
findstr /C:"AUTO_DISCOVERY_ENABLED=true" backend\.env >nul 2>&1
if %errorlevel% equ 0 (
    echo [+] Auto-discovery: ENABLED
    echo     ^(New project folders will import automatically^)
) else (
    echo [i] Auto-discovery: Disabled
    echo     ^(Enable in backend\.env to auto-import new projects^)
)

:config_done
echo.

echo Starting Backend Server...

REM Try venv (standard)
if exist "backend\venv\Scripts\activate.bat" (
    echo Using virtual environment ^(backend\venv^)...
    start "Backend Server" cmd /k "cd backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
    goto :backend_started
)

REM Try .venv (common alternative)
if exist "backend\.venv\Scripts\activate.bat" (
    echo Using virtual environment ^(backend\.venv^)...
    start "Backend Server" cmd /k "cd backend && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
    goto :backend_started
)

echo WARNING: No virtual environment found at backend\venv or backend\.venv
echo          Using system Python — ensure dependencies are installed globally.
start "Backend Server" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

:backend_started
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
echo Press any key to exit ^(servers will keep running^)
pause >nul
