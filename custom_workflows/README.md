# Custom Workflows

High-quality 3D generation workflows with face processing, image enhancement, and automatic texture extraction.

## 🎨 NEW: Graphical User Interface

**Easy-to-use GUI for all workflows!**

### Launch GUI

**Windows:**
```bash
launch_gui.bat
```

**Linux/Mac:**
```bash
chmod +x launch_gui.sh
./launch_gui.sh
```

**Or directly:**
```bash
python custom_workflows_gui.py
```

### GUI Features

- **🖼️ Single Image Tab**: Process single images with all enhancements
- **📐 Multiview Tab**: Generate from multiple views (front/back/left/right)
- **📦 Batch Processing Tab**: Process multiple images at once
- **🎨 Texture Extraction Tab**: Extract textures from existing models
- **⚙️ Settings Panel**: Configure all parameters (model, steps, resolution, export formats)
- **Visual Preview**: See textures and download results directly

## Installation

### Quick Install (Recommended)
```bash
# All required dependencies (includes face detection and image enhancement)
uv pip install pyyaml gradio facexlib kornia

# Or use the automatic installer (Windows)
install_dependencies.bat
```

### What Gets Installed:
- ✅ **pyyaml**: Configuration file support
- ✅ **gradio**: Web-based GUI framework
- ✅ **facexlib**: Face detection and alignment for portraits
- ✅ **kornia**: Image sharpening and illumination normalization

### Already Have Main Project?
If you've already installed the main project dependencies:
```bash
# Just install GUI-specific packages
uv pip install pyyaml gradio
```

The main requirements.txt now includes facexlib and kornia by default.

## Quick Start

### GUI (Recommended)
```bash
# Launch GUI
python custom_workflows_gui.py
```

### Command Line
```bash
# Single image → OBJ + PNG (best quality)
python complete_workflow.py input.jpg

# Portrait (auto face detection)
python complete_workflow.py portrait.jpg --portrait

# Multi-view
python multiview_workflow.py --front f.jpg --back b.jpg

# Batch processing
python batch_workflow.py folder/

# Extract texture from existing model
python extract_texture.py model.glb
```

## Usage

### Single Image Workflow
```bash
python complete_workflow.py input.jpg [--portrait] [--output-dir OUTPUT] [--model mini]
```

**Features:**
- Auto face detection & alignment (if `--portrait`)
- Image enhancement (sharpening + illumination)
- Background removal
- High-quality mesh (384 octree, 50 steps)
- 2K texture (2048x2048)
- Exports: OBJ + PNG + GLB

### Multi-View Workflow
```bash
python multiview_workflow.py --front f.jpg --back b.jpg [--left l.jpg] [--right r.jpg]
```

### Batch Processing
```bash
python batch_workflow.py folder/ [--parallel 2]
python batch_workflow.py img1.jpg img2.jpg img3.jpg
```

### Universal Launcher
```bash
python launcher.py single input.jpg
python launcher.py multiview --front f.jpg --back b.jpg
python launcher.py batch folder/
```

### Texture Extraction
```bash
python extract_texture.py textured_mesh.glb [output.png]
# Or drag-and-drop GLB file onto extract_texture.bat
```

## Quality Settings

**Default (Best Quality):**
- Model: Full H2 (2.6B parameters)
- Steps: 50, Guidance: 7.5, Octree: 384
- Texture: 2048px, Faces: 50k
- Enhancements: Enabled (1.5x sharpness, illumination normalization)

**Customize:** Edit `workflow_config.yaml`

## Files

**GUI:**
- `custom_workflows_gui.py` - **NEW!** Graphical user interface (recommended)
- `launch_gui.bat` - Windows launcher
- `launch_gui.sh` - Linux/Mac launcher

**Core Scripts:**
- `complete_workflow.py` - Single image pipeline
- `multiview_workflow.py` - Multi-view pipeline
- `batch_workflow.py` - Batch processing
- `launcher.py` - CLI menu launcher
- `extract_texture.py` - Texture extractor
- `extract_texture.bat` - Drag-and-drop extractor

**Examples:**
- `example_extract_texture.py` - Full workflow example
- `example_with_face_kornia.py` - Face/enhancement example

**Configuration:**
- `workflow_config.yaml` - All settings (edit to customize, used by GUI)

## Requirements

- Minimum: RTX 3090 (24GB VRAM), 32GB RAM
- Recommended: RTX 4090 (48GB VRAM), 64GB RAM
- Lower VRAM: Use `--model mini` flag

## Output

Workflows generate:
- `output/{name}_textured.obj` - 3D mesh
- `output/{name}_texture.png` - 2K texture (2048x2048)
- `output/{name}_textured.glb` - GLB file (optional)
