@echo off
REM ============================================================================
REM Conduital Build Script
REM
REM Builds the packaged Windows executable:
REM   1. Builds frontend (npm run build)
REM   2. Runs PyInstaller (creates dist/Conduital/)
REM
REM Prerequisites:
REM   - Node.js + npm installed
REM   - Python venv with pyinstaller, pystray, Pillow installed
REM   - Frontend dependencies installed (npm install)
REM
REM Usage:
REM   build.bat              Full build (frontend + backend)
REM   build.bat --skip-fe    Skip frontend build (use existing dist/)
REM   build.bat --clean      Clean previous build artifacts first
REM ============================================================================

setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0
set BACKEND_DIR=%PROJECT_ROOT%backend
set FRONTEND_DIR=%PROJECT_ROOT%frontend
set VENV_PYTHON=%BACKEND_DIR%\venv\Scripts\python.exe

echo.
echo  ============================================
echo   Conduital Build
echo  ============================================
echo.

REM Parse arguments
set SKIP_FE=0
set CLEAN=0
for %%a in (%*) do (
    if "%%a"=="--skip-fe" set SKIP_FE=1
    if "%%a"=="--clean" set CLEAN=1
)

REM Clean previous build if requested
if %CLEAN%==1 (
    echo  [1/4] Cleaning previous build...
    if exist "%BACKEND_DIR%\build" rmdir /s /q "%BACKEND_DIR%\build"
    if exist "%BACKEND_DIR%\dist" rmdir /s /q "%BACKEND_DIR%\dist"
    echo        Done.
) else (
    echo  [1/4] Clean skipped (use --clean to remove old artifacts^)
)

REM Build frontend
if %SKIP_FE%==0 (
    echo  [2/4] Building frontend...
    cd /d "%FRONTEND_DIR%"

    if not exist "node_modules" (
        echo        Installing npm dependencies...
        call npm install
        if errorlevel 1 (
            echo  ERROR: npm install failed
            exit /b 1
        )
    )

    call npm run build
    if errorlevel 1 (
        echo  ERROR: Frontend build failed
        exit /b 1
    )
    echo        Done.
) else (
    echo  [2/4] Frontend build skipped (--skip-fe^)
    if not exist "%FRONTEND_DIR%\dist" (
        echo  ERROR: frontend/dist not found. Run without --skip-fe first.
        exit /b 1
    )
)

REM Verify frontend dist exists
if not exist "%FRONTEND_DIR%\dist\index.html" (
    echo  ERROR: frontend/dist/index.html not found. Frontend build may have failed.
    exit /b 1
)

REM Run PyInstaller
echo  [3/4] Running PyInstaller...
cd /d "%BACKEND_DIR%"

if not exist "%VENV_PYTHON%" (
    echo  ERROR: Python venv not found at %VENV_PYTHON%
    echo  Create it with: python -m venv venv ^&^& venv\Scripts\pip install -r requirements.txt pyinstaller pystray Pillow
    exit /b 1
)

"%VENV_PYTHON%" -m PyInstaller conduital.spec --clean --noconfirm
if errorlevel 1 (
    echo  ERROR: PyInstaller build failed
    exit /b 1
)
echo        Done.

REM Report results
echo  [4/4] Build complete!
echo.
echo  ============================================
echo   Output: backend\dist\Conduital\
echo   Launch: backend\dist\Conduital\Conduital.exe
echo  ============================================
echo.

REM Show size
set TOTAL_BYTES=0
for /f "usebackq tokens=3,4" %%a in (`dir "%BACKEND_DIR%\dist\Conduital" /s /-c 2^>nul ^| findstr /c:"File(s)"`) do (
    set TOTAL_BYTES=%%a
)
if !TOTAL_BYTES! GTR 0 (
    set /a SIZE_MB=!TOTAL_BYTES! / 1048576
    echo   Total size: ~!SIZE_MB! MB ^(!TOTAL_BYTES! bytes^)
) else (
    echo   Total size: unknown
)
echo.

endlocal
