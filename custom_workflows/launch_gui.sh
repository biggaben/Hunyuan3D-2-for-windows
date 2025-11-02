#!/bin/bash
# Launch Custom Workflows GUI for Unix/Linux/Mac
# ==============================================

echo "==============================================================================="
echo "  Hunyuan3D-2 Custom Workflows GUI"
echo "==============================================================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check for required dependencies
echo "Checking dependencies..."
MISSING_DEPS=""

python3 -c "import yaml" 2>/dev/null || MISSING_DEPS="$MISSING_DEPS pyyaml"
python3 -c "import gradio" 2>/dev/null || MISSING_DEPS="$MISSING_DEPS gradio"
python3 -c "import facexlib" 2>/dev/null || MISSING_DEPS="$MISSING_DEPS facexlib"
python3 -c "import kornia" 2>/dev/null || MISSING_DEPS="$MISSING_DEPS kornia"

if [ ! -z "$MISSING_DEPS" ]; then
    echo ""
    echo "Missing dependencies:$MISSING_DEPS"
    echo ""
    echo "Installing missing dependencies..."
    pip3 install$MISSING_DEPS
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to install dependencies"
        echo "Please run manually: pip3 install$MISSING_DEPS"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo ""
    echo "Dependencies installed successfully!"
fi

echo "Dependencies OK"
echo ""
echo "Starting Custom Workflows GUI..."
echo ""

python3 custom_workflows_gui.py "$@"

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: GUI failed to start. Check the error messages above."
    echo ""
    echo "Common issues:"
    echo "  - Missing dependencies: pip3 install pyyaml gradio facexlib kornia"
    echo "  - CUDA not available: Set device to 'cpu' in workflow_config.yaml"
    echo "  - Model not downloaded: First run downloads ~10GB models"
    read -p "Press Enter to exit..."
fi

