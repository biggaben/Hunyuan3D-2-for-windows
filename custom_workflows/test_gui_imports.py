#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify GUI imports and basic initialization.
This doesn't run the full workflows (which require GPU), 
just checks that all imports work and UI can be created.
"""

import sys
import io
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*70)
print("Testing Custom Workflows GUI - Import Check")
print("="*70)
print()

# Test 1: Import main GUI module
print("[1/6] Testing GUI module import...")
try:
    from custom_workflows_gui import CustomWorkflowsGUI, WorkflowConfig
    print("✓ GUI module imported successfully")
except Exception as e:
    print(f"✗ Failed to import GUI module: {e}")
    sys.exit(1)

# Test 2: Import workflow modules
print("\n[2/6] Testing workflow module imports...")
try:
    from complete_workflow import Hunyuan3DCompleteWorkflow
    from multiview_workflow import Hunyuan3DMultiviewWorkflow
    from extract_texture import extract_texture_from_mesh
    print("✓ Workflow modules imported successfully")
except Exception as e:
    print(f"✗ Failed to import workflow modules: {e}")
    sys.exit(1)

# Test 3: Import Gradio
print("\n[3/6] Testing Gradio import...")
try:
    import gradio as gr
    print(f"✓ Gradio {gr.__version__} imported successfully")
except Exception as e:
    print(f"✗ Failed to import Gradio: {e}")
    print("   Install with: pip install gradio")
    sys.exit(1)

# Test 4: Test WorkflowConfig
print("\n[4/6] Testing configuration manager...")
try:
    config_manager = WorkflowConfig()
    config = config_manager.config
    assert 'model' in config
    assert 'generation' in config
    assert 'export' in config
    print("✓ Configuration manager initialized successfully")
    print(f"   Model type: {config['model']['type']}")
    print(f"   Device: {config['model']['device']}")
    print(f"   Octree resolution: {config['generation']['octree_resolution']}")
except Exception as e:
    print(f"✗ Failed to initialize configuration: {e}")
    sys.exit(1)

# Test 5: Test GUI initialization
print("\n[5/6] Testing GUI initialization...")
try:
    app = CustomWorkflowsGUI()
    print("✓ GUI application initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize GUI: {e}")
    sys.exit(1)

# Test 6: Test UI creation (without launching)
print("\n[6/6] Testing UI creation...")
try:
    demo = app.create_ui()
    print("✓ UI created successfully")
    print(f"   UI type: {type(demo)}")
except Exception as e:
    print(f"✗ Failed to create UI: {e}")
    sys.exit(1)

print("\n" + "="*70)
print("✅ All tests passed! GUI is ready to launch.")
print("="*70)
print("\nTo launch the GUI, run:")
print("  python custom_workflows_gui.py")
print("  or")
print("  ./launch_gui.bat (Windows)")
print("  ./launch_gui.sh (Linux/Mac)")
print()

