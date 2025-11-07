# Hunyuan3D-2 Project Overview

## Project Structure

### Main Components
- **gradio_app.py**: Main official GUI with 3D viewer, seed control, example galleries
- **custom_workflows/custom_workflows_gui.py**: Custom workflows GUI with better organization, batch processing
- **hy3dgen/**: Core generation library
  - `shapegen/`: Shape generation pipelines and postprocessors
  - `texgen/`: Texture generation pipelines
  - `text2image.py`: Text-to-image pipeline (optional)

### Key Workflows
1. **Single Image → 3D**: Complete workflow with enhancements
2. **Multiview → 3D**: Multiple views (front/back/left/right)
3. **Batch Processing**: Process multiple images
4. **Texture Extraction**: Extract textures from existing models

## Available Models
- **H2 (Full)**: 2.6B parameters, maximum quality, requires 24GB+ VRAM
- **H2 Mini**: 0.6B parameters, faster, requires 8-12GB VRAM
- **H2 MV**: Multiview model, requires 16GB+ VRAM
- **H2 Turbo**: Fast variant with slight quality tradeoff

## High Quality Generation Settings

### Critical Settings for Maximum Quality
- **Model**: H2 (Full 2.6B)
- **Inference Steps**: 50-100
- **Guidance Scale**: 7.5-10.0
- **Octree Resolution**: 384-512
- **Number of Chunks**: 20,000+
- **Texture Resolution**: 2048x2048
- **Face Processing**: Enabled
- **Image Enhancement**: Enabled (sharpness 1.5, normalize illumination)

### Hidden Settings Not Exposed in GUI
- Border ratio control (hardcoded to 0.2)
- Face processing: confidence threshold, padding
- Image enhancement: sharpness factor, individual toggles
- Texture: render_size, texture_size, target_face_count
- Post-processing: floater removal, degenerate face removal
- Number of chunks (missing in custom workflows GUI)
- Seed control (missing in custom workflows GUI)

## GUI Comparison

### Main Gradio App Strengths
- Interactive 3D viewer
- Seed control + randomization
- Example galleries
- Statistics panel
- Background removal toggle
- Turbo/Fast/Standard presets

### Custom Workflows GUI Strengths
- Better organization (tabs)
- Batch processing
- Texture extraction workflow
- Settings accordion
- YAML config integration

## Enhancement Opportunities

See `ANALYSIS_HIGH_QUALITY_SETTINGS_AND_GUI_UPGRADES.md` for complete analysis of:
- 57+ possible enhancements
- 20+ settings not exposed in GUI
- Detailed implementation roadmap
- Priority matrix (impact vs effort)

## User Defined Namespaces
- [Leave blank - user populates]

