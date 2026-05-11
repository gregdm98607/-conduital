@echo off
REM ============================================================================
REM Conduital Installer Build
REM
REM Reads version from backend\pyproject.toml (single source of truth) and
REM compiles installer\conduital.iss into installer\Output\ConduitalSetup-X.Y.Z.exe.
REM
REM Prerequisites:
REM   - backend\dist\Conduital\Conduital.exe must already exist (run build.bat first)
REM   - Inno Setup 6.x installed (https://jrsoftware.org/isinfo.php)
REM ============================================================================

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PYPROJECT=%PROJECT_ROOT%\backend\pyproject.toml
set ISS_FILE=%SCRIPT_DIR%conduital.iss

if not exist "%PYPROJECT%" (
    echo ERROR: %PYPROJECT% not found
    exit /b 1
)

REM Extract version from pyproject.toml (first 'version = "x.y.z"' line)
set VERSION=
for /f "tokens=2 delims== " %%a in ('findstr /b /c:"version = " "%PYPROJECT%"') do (
    if not defined VERSION (
        set RAW=%%a
        set VERSION=!RAW:"=!
    )
)

if not defined VERSION (
    echo ERROR: could not parse version from %PYPROJECT%
    exit /b 1
)

echo Building installer for Conduital !VERSION!

REM Locate ISCC — Program Files install, or scoop shim on PATH
set ISCC=
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe
if not defined ISCC for /f "delims=" %%a in ('where iscc 2^>nul') do if not defined ISCC set ISCC=%%a

if not defined ISCC (
    echo ERROR: Inno Setup 6 not found. Install with 'scoop install extras/inno-setup'.
    exit /b 1
)

"%ISCC%" /DMyAppVersion=!VERSION! "%ISS_FILE%"
if errorlevel 1 (
    echo ERROR: ISCC compile failed
    exit /b 1
)

echo.
echo Installer built: %SCRIPT_DIR%Output\ConduitalSetup-!VERSION!.exe
endlocal
