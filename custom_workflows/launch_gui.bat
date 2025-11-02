@echo off
REM Launch Custom Workflows GUI for Windows
REM ========================================

echo ===============================================================================
echo   Hunyuan3D-2 Custom Workflows GUI
echo ===============================================================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check for required dependencies
echo Checking dependencies...

set MISSING_DEPS=

python -c "import yaml" >nul 2>&1
if errorlevel 1 set MISSING_DEPS=%MISSING_DEPS% pyyaml

python -c "import gradio" >nul 2>&1
if errorlevel 1 set MISSING_DEPS=%MISSING_DEPS% gradio

python -c "import facexlib" >nul 2>&1
if errorlevel 1 set MISSING_DEPS=%MISSING_DEPS% facexlib

python -c "import kornia" >nul 2>&1
if errorlevel 1 set MISSING_DEPS=%MISSING_DEPS% kornia

if not "%MISSING_DEPS%"=="" (
    echo.
    echo Missing dependencies:%MISSING_DEPS%
    echo.
    echo Installing missing dependencies...
    uv pip install%MISSING_DEPS%
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies
        echo Please run manually: uv pip install%MISSING_DEPS%
        pause
        exit /b 1
    )
    echo.
    echo Dependencies installed successfully!
)

echo Dependencies OK
echo.
echo Starting Custom Workflows GUI...
echo.

python custom_workflows_gui.py %*

if errorlevel 1 (
    echo.
    echo ERROR: GUI failed to start. Check the error messages above.
    echo.
    echo Common issues:
    echo   - Missing dependencies: uv pip install pyyaml gradio
    echo   - CUDA not available: Set device to 'cpu' in workflow_config.yaml
    echo   - Model not downloaded: First run downloads ~10GB models
    pause
)

