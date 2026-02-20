@echo off
echo Starting Conduital Development Servers...
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
timeout /t 3 /nobreak >nul

echo Starting Frontend Server...
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Development servers starting...
echo ========================================
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo ========================================
echo.
echo Press any key to exit (servers will keep running)
pause >nul
