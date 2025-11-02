@echo off
REM Windows batch script to extract texture from GLB files
REM Drag and drop a GLB file onto this batch file to extract its texture

if "%~1"=="" (
    echo.
    echo Usage: Drag and drop a textured mesh file ^(GLB/OBJ^) onto this batch file
    echo Or run: extract_texture.bat "path\to\textured_mesh.glb"
    echo.
    pause
    exit /b 1
)

echo Extracting texture from: %~1
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Run the extraction script
python extract_texture.py "%~1"

echo.
pause

