@echo off
REM Install Custom Workflows GUI Dependencies
REM =========================================

echo ===============================================================================
echo   Installing Custom Workflows GUI Dependencies
echo ===============================================================================
echo.

cd /d "%~dp0"

REM Check if uv is available
uv --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv not found. Installing with pip...
    python -m pip install pyyaml gradio
) else (
    echo Using uv package manager...
    uv pip install pyyaml gradio
)

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install core dependencies
    pause
    exit /b 1
)

echo.
echo Installing custom workflow enhancements...
if exist "C:\Windows\System32\where.exe" (
    where uv >nul 2>&1
    if errorlevel 1 (
        python -m pip install facexlib kornia
    ) else (
        uv pip install facexlib kornia
    )
) else (
    uv pip install facexlib kornia
)

echo.
echo ===============================================================================
echo   All dependencies installed successfully!
echo ===============================================================================
echo.
echo Installed:
echo   - pyyaml (YAML configuration)
echo   - gradio (Web UI)
echo   - facexlib (Face detection and alignment)
echo   - kornia (Image enhancement)
echo.
echo To launch GUI, run:
echo   launch_gui.bat
echo.
pause

