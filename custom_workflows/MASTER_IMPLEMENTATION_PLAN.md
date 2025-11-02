# Master Implementation Plan
## Multi-Model Integration for Custom Workflows GUI

**Version**: 1.0  
**Date**: November 2, 2025  
**Status**: Ready for Implementation  
**Total Timeline**: 8-10 weeks  

---

## 📋 **Executive Summary**

This document outlines the complete implementation plan for integrating 6 new models/variants into the Hunyuan3D-2 Custom Workflows GUI:

1. **Hunyuan3D-2.1** - PBR materials (production-ready)
2. **TripoSR** - Ultra-fast draft mode (0.5s)
3. **TRELLIS** - Microsoft's popular alternative (2.5M downloads)
4. **Hunyuan3D-Omni** - Multi-modal control (point/pose/bbox)
5. **Hunyuan3D-Part** - Part segmentation and editing
6. **InstantMesh** - Auto multi-view generation

**Priority**: Focus on highest-impact, lowest-effort integrations first.

---

## 🏗️ **Current Architecture Analysis**

### **Existing Codebase Structure:**

```python
custom_workflows/
├── complete_workflow.py        # Single image workflow class
├── multiview_workflow.py       # Multi-view workflow class
├── batch_workflow.py           # Batch processing
├── extract_texture.py          # Texture extraction
├── custom_workflows_gui.py     # Gradio GUI (main)
├── workflow_config.yaml        # Configuration
└── launcher.py                 # CLI launcher
```

### **Key Pattern Identified:**

```python
class Hunyuan3DCompleteWorkflow:
    def __init__(self, model_path='tencent/Hunyuan3D-2', device='cuda', ...):
        # Load model from HuggingFace
        self.pipeline_shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            model_path,
            subfolder='hunyuan3d-dit-v2-0'  # or variant
        )
        # Load texture model
        self.pipeline_tex = Hunyuan3DPaintPipeline.from_pretrained('tencent/Hunyuan3D-2')
    
    def process_single_image(self, image_path, output_dir='outputs', ...):
        # Processing logic
        return results
```

### **GUI Integration Pattern:**

```python
class CustomWorkflowsGUI:
    def __init__(self):
        self.workflow_single = None  # Lazy load
        
    def initialize_workflow_single(self, model_type, ...):
        model_path = 'tencent/Hunyuan3D-2' if model_type == 'h2' else 'tencent/Hunyuan3D-2mini'
        self.workflow_single = Hunyuan3DCompleteWorkflow(model_path=model_path, ...)
    
    def create_ui(self):
        with gr.Blocks() as demo:
            model_type = gr.Radio(choices=['h2', 'mini'], ...)
            # Process button calls self.process_single_image()
```

---

## 📊 **Implementation Dependency Graph**

```
Foundation:
├─ Hunyuan3D-2.1 ────────────┐
│                             │
Parallel Independent:         │
├─ TripoSR                    │
├─ TRELLIS (test first)       │
│                             ↓
Depends on 2.1:          Extensions:
├─ Hunyuan3D-Omni ──────> Extends H3D
├─ Hunyuan3D-Part ──────> Extends H3D
│
Optional:
└─ InstantMesh
```

**Dependencies:**
- **Omni** and **Part** should use 2.1 as base (may have PBR support)
- **TripoSR** and **TRELLIS** are independent
- **InstantMesh** is independent

---

## 🎯 **Implementation Plan by Phase**

### **Phase 1: Foundation (Week 1)** ⭐⭐⭐⭐⭐

#### **1.1 Upgrade to Hunyuan3D-2.1** (2-3 hours)

**Priority**: CRITICAL - Required for all future Hunyuan models

**Changes Required:**

**File: `workflow_config.yaml`**
```yaml
model:
  type: 'h21'  # NEW: Default to 2.1
  path_h21: 'tencent/Hunyuan3D-2.1'  # NEW
  path_h2: 'tencent/Hunyuan3D-2'      # Legacy
  path_mini: 'tencent/Hunyuan3D-2mini'
  
export:
  formats: ['glb', 'obj']
  pbr_export: true  # NEW: PBR material maps
  pbr_resolution: 2048  # NEW
```

**File: `complete_workflow.py`**
```python
class Hunyuan3DCompleteWorkflow:
    def __init__(self, model_path='tencent/Hunyuan3D-2.1', ...):  # Changed default
        # Detect PBR support
        self.supports_pbr = '2.1' in model_path or '2.5' in model_path
        # Existing initialization...
    
    def export_pbr_materials(self, output_path):
        """NEW: Export PBR material maps"""
        if not self.supports_pbr:
            return None
        
        # Extract from model outputs
        pbr_maps = {
            'albedo': self.extract_albedo(),
            'normal': self.extract_normal(),
            'roughness': self.extract_roughness(),
            'metallic': self.extract_metallic(),
            'ao': self.extract_ao()
        }
        
        for map_type, map_data in pbr_maps.items():
            save_path = output_path / f"{map_type}.png"
            Image.fromarray(map_data).save(save_path)
        
        return pbr_maps
```

**File: `custom_workflows_gui.py`**
```python
# In create_ui()
model_type = gr.Radio(
    choices=[
        ('h21', 'Hunyuan3D-2.1 (PBR Materials)'),  # NEW - Default
        ('h2', 'Hunyuan3D-2.0 (Legacy)'),
        ('mini', 'Hunyuan3D-2mini (Fast)')
    ],
    value='h21',  # NEW default
    label="Model Version"
)

# NEW: PBR export options (only show for 2.1)
with gr.Accordion("PBR Material Export", open=False, visible=True) as pbr_accordion:
    export_pbr = gr.Checkbox(label="Export PBR Maps", value=True)
    pbr_resolution = gr.Radio(
        choices=['1024', '2048', '4096'],
        value='2048',
        label="PBR Resolution"
    )

# Update visibility based on model selection
def update_pbr_visibility(model_type):
    return gr.update(visible=('21' in model_type))

model_type.change(
    fn=update_pbr_visibility,
    inputs=[model_type],
    outputs=[pbr_accordion]
)
```

**Testing:**
```bash
# Test 2.1 generation
python custom_workflows_gui.py
# Select h21 model
# Generate test image
# Verify outputs: albedo.png, normal.png, roughness.png, metallic.png, ao.png
```

**Success Criteria:**
- ✅ Model loads successfully
- ✅ PBR maps export correctly
- ✅ All 5 maps present (albedo, normal, roughness, metallic, AO)
- ✅ Resolution is 2048x2048
- ✅ Backward compatibility maintained (h2, mini still work)

---

#### **1.2 Testing Infrastructure** (1 day)

**NEW File: `custom_workflows/benchmark_models.py`**
```python
#!/usr/bin/env python3
"""
Model Benchmarking Tool
Compare speed, quality, and VRAM usage across models
"""

import time
import torch
import psutil
from pathlib import Path
from PIL import Image

class ModelBenchmark:
    def __init__(self, test_images_dir='benchmark_images/'):
        self.test_images = list(Path(test_images_dir).glob('*.{jpg,png}'))
    
    def benchmark_model(self, workflow_class, model_path, **kwargs):
        """Benchmark a single model"""
        results = {
            'model': model_path,
            'times': [],
            'vram_peak': 0,
            'outputs': []
        }
        
        # Initialize workflow
        workflow = workflow_class(model_path=model_path, **kwargs)
        
        for img_path in self.test_images:
            # Clear cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
            
            # Benchmark
            start = time.time()
            output = workflow.process_single_image(str(img_path))
            elapsed = time.time() - start
            
            # Record
            results['times'].append(elapsed)
            results['outputs'].append(output)
            
            if torch.cuda.is_available():
                peak_mb = torch.cuda.max_memory_allocated() / 1024 / 1024
                results['vram_peak'] = max(results['vram_peak'], peak_mb)
        
        return results
    
    def compare_models(self, models_config):
        """Compare multiple models"""
        all_results = []
        
        for config in models_config:
            print(f"\nBenchmarking {config['name']}...")
            results = self.benchmark_model(**config)
            results['name'] = config['name']
            all_results.append(results)
        
        # Generate report
        self.generate_report(all_results)
        
        return all_results
    
    def generate_report(self, results):
        """Generate comparison report"""
        print("\n" + "="*70)
        print("BENCHMARK RESULTS")
        print("="*70)
        
        for r in results:
            avg_time = sum(r['times']) / len(r['times'])
            print(f"\n{r['name']}:")
            print(f"  Avg Time: {avg_time:.2f}s")
            print(f"  Peak VRAM: {r['vram_peak']:.0f} MB")
            print(f"  Model: {r['model']}")

if __name__ == '__main__':
    benchmark = ModelBenchmark()
    
    models = [
        {
            'name': 'Hunyuan3D-2.0',
            'workflow_class': Hunyuan3DCompleteWorkflow,
            'model_path': 'tencent/Hunyuan3D-2'
        },
        {
            'name': 'Hunyuan3D-2.1',
            'workflow_class': Hunyuan3DCompleteWorkflow,
            'model_path': 'tencent/Hunyuan3D-2.1'
        },
        # More models will be added as integrated
    ]
    
    benchmark.compare_models(models)
```

**Usage:**
```bash
# Create benchmark images
mkdir benchmark_images
# Add 5-10 test images

# Run benchmark
python benchmark_models.py
```

---

#### **1.3 TRELLIS Evaluation** (2-3 days)

**Priority**: HIGH - Must test before committing to integration

**NEW File: `custom_workflows/trellis_workflow.py`**
```python
#!/usr/bin/env python3
"""
TRELLIS Model Wrapper
Microsoft's structured latent 3D generation
"""

import torch
from pathlib import Path

# Will need to install: pip install trellis-3d (or similar)
try:
    from trellis import TRELLISPipeline
    TRELLIS_AVAILABLE = True
except ImportError:
    print("⚠️  TRELLIS not available")
    TRELLIS_AVAILABLE = False

class TRELLISWorkflow:
    """TRELLIS 3D generation workflow"""
    
    def __init__(self, 
                 model_path='microsoft/TRELLIS-image-large',
                 device='cuda'):
        """
        Initialize TRELLIS workflow
        
        Args:
            model_path: HuggingFace model path
            device: 'cuda' or 'cpu'
        """
        if not TRELLIS_AVAILABLE:
            raise ImportError("TRELLIS not installed")
        
        self.device = device
        
        print("="*70)
        print("Initializing TRELLIS (Microsoft)")
        print("="*70)
        
        # Load TRELLIS model
        print(f"✓ Loading {model_path}...")
        self.pipeline = TRELLISPipeline.from_pretrained(
            model_path,
            device=device
        )
        
        print("="*70)
        print("Initialization complete!")
        print("="*70)
    
    def process_single_image(self, image_path, output_dir='outputs'):
        """
        Process single image through TRELLIS
        
        Args:
            image_path: Path to input image
            output_dir: Output directory
            
        Returns:
            Dict with output file paths
        """
        from PIL import Image
        
        # Load image
        image = Image.open(image_path)
        
        # Generate 3D
        print("Generating 3D model with TRELLIS...")
        output = self.pipeline(image)
        
        # Export
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save mesh
        glb_path = output_dir / "model.glb"
        output.export(str(glb_path))
        
        return {
            'glb': str(glb_path),
            'model': output
        }
```

**Testing Plan:**
```python
# Add to benchmark_models.py
{
    'name': 'TRELLIS',
    'workflow_class': TRELLISWorkflow,
    'model_path': 'microsoft/TRELLIS-image-large'
}
```

**Decision Matrix:**
```
After testing:
- Speed: < 30s → ⭐⭐⭐⭐⭐ Integrate as primary
- Speed: 30-120s → ⭐⭐⭐⭐ Integrate as alternative
- Speed: > 120s → ⭐⭐ Skip or low priority

- Quality: Better than H3D-2.1 → Primary model
- Quality: Similar to H3D-2.1 → User choice
- Quality: Worse than H3D-2.1 → Skip

- Features: Has PBR → ⭐⭐⭐⭐⭐
- Features: No PBR → ⭐⭐⭐
```

---

### **Phase 2: Speed Layer (Week 2)** ⭐⭐⭐⭐⭐

#### **2.1 TripoSR Integration** (3 days)

**Priority**: CRITICAL - Massive UX improvement

**NEW File: `custom_workflows/triposr_workflow.py`**
```python
#!/usr/bin/env python3
"""
TripoSR Fast 3D Generation Workflow
Ultra-fast feed-forward LRM model (0.5s generation!)
"""

import torch
from pathlib import Path
from PIL import Image

try:
    from tsr.system import TSR
    TRIPOSR_AVAILABLE = True
except ImportError:
    print("⚠️  TripoSR not available. Install: pip install triposr")
    TRIPOSR_AVAILABLE = False

class TripoSRWorkflow:
    """TripoSR ultra-fast workflow"""
    
    def __init__(self,
                 model_path='stabilityai/TripoSR',
                 device='cuda',
                 chunk_size=8192):
        """
        Initialize TripoSR
        
        Args:
            model_path: Model path (local or HuggingFace)
            device: 'cuda' or 'cpu'
            chunk_size: Marching cubes chunk size
        """
        if not TRIPOSR_AVAILABLE:
            raise ImportError("TripoSR not installed")
        
        self.device = device
        self.chunk_size = chunk_size
        
        print("="*70)
        print("Initializing TripoSR - ULTRA FAST MODE")
        print("="*70)
        print("Expected speed: 0.5-1.0 seconds per image!")
        print("="*70)
        
        # Load model
        print(f"✓ Loading {model_path}...")
        self.model = TSR.from_pretrained(
            model_path,
            config_name="config.yaml",
            weight_name="model.ckpt",
        )
        self.model.renderer.set_chunk_size(chunk_size)
        self.model.to(device)
        
        print("="*70)
        print("Initialization complete!")
        print("="*70)
    
    def process_single_image(self, image_path, output_dir='outputs'):
        """
        Process image with TripoSR (0.5s!)
        
        Args:
            image_path: Input image path
            output_dir: Output directory
            
        Returns:
            Dict with output paths
        """
        import numpy as np
        from rembg import remove
        
        # Load and preprocess
        image = Image.open(image_path)
        
        # Remove background if needed
        if image.mode == 'RGB':
            image = remove(image, alpha_matting=True)
        
        # Resize to 512x512 (TripoSR input)
        image = image.resize((512, 512), Image.LANCZOS)
        
        # Generate mesh (FAST!)
        print("⚡ Generating with TripoSR (0.5s)...")
        with torch.no_grad():
            scene_codes = self.model([image], device=self.device)
        
        # Extract mesh
        meshes = self.model.extract_mesh(scene_codes, resolution=256)
        
        # Export
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        glb_path = output_dir / "model.glb"
        meshes[0].export(str(glb_path))
        
        return {
            'glb': str(glb_path),
            'mesh': meshes[0]
        }
```

**Installation:**
```bash
# Add to requirements.txt
triposr  # TripoSR model

# Or manual install
pip install git+https://github.com/VAST-AI-Research/TripoSR.git
```

---

#### **2.2 GUI Integration - Quality Presets** (1 day)

**File: `custom_workflows/custom_workflows_gui.py`**
```python
# NEW: Quality preset system
class CustomWorkflowsGUI:
    def __init__(self):
        # ... existing code ...
        self.workflow_triposr = None  # NEW
    
    def initialize_workflow_by_preset(self, preset, device):
        """Initialize workflow based on quality preset"""
        presets = {
            'draft': {
                'workflow_class': TripoSRWorkflow,
                'model_path': 'stabilityai/TripoSR',
                'name': 'TripoSR (Draft)',
                'expected_time': '0.5s'
            },
            'preview': {
                'workflow_class': Hunyuan3DCompleteWorkflow,
                'model_path': 'tencent/Hunyuan3D-2mini',
                'name': 'Hunyuan3D-2mini',
                'expected_time': '30s'
            },
            'balanced': {
                'workflow_class': Hunyuan3DCompleteWorkflow,
                'model_path': 'tencent/Hunyuan3D-2.1',
                'name': 'Hunyuan3D-2.1',
                'expected_time': '2min'
            },
            'quality': {
                'workflow_class': Hunyuan3DCompleteWorkflow,
                'model_path': 'tencent/Hunyuan3D-2.1',
                'name': 'Hunyuan3D-2.1 (Max Quality)',
                'expected_time': '5min',
                'steps': 100
            }
        }
        
        config = presets[preset]
        workflow = config['workflow_class'](
            model_path=config['model_path'],
            device=device,
            **config.get('extra_params', {})
        )
        
        return workflow, config['name'], config['expected_time']
    
    def create_ui(self):
        with gr.Blocks() as demo:
            # ... existing code ...
            
            # NEW: Quality preset selector (replaces simple model selector)
            quality_preset = gr.Radio(
                choices=[
                    ('draft', '⚡ Draft (0.5s - TripoSR)'),
                    ('preview', '🔹 Preview (30s - Mini)'),
                    ('balanced', '⭐ Balanced (2min - H3D 2.1)'),
                    ('quality', '💎 Quality (5min - H3D 2.1 Max)')
                ],
                value='balanced',
                label="Quality Preset",
                info="Choose speed vs quality tradeoff"
            )
            
            # Advanced model selection (collapsible)
            with gr.Accordion("🔧 Advanced Model Selection", open=False):
                model_type = gr.Radio(
                    choices=[
                        ('h21', 'Hunyuan3D-2.1'),
                        ('h2', 'Hunyuan3D-2.0'),
                        ('mini', 'Hunyuan3D-2mini'),
                        ('triposr', 'TripoSR'),
                        ('trellis', 'TRELLIS')  # If integrated
                    ],
                    value='h21',
                    label="Specific Model"
                )
```

---

### **Phase 3: TRELLIS Decision (Week 3)**

**Based on Phase 1 testing results:**

#### **Option A: TRELLIS is Excellent → Integrate** (1 week)

```python
# Add to GUI model options
('trellis', 'TRELLIS (Microsoft)'),

# Create trellis_workflow.py (already drafted in Phase 1)
# Add to quality presets if fast
# Update documentation
```

#### **Option B: TRELLIS is Mediocre → Skip**

```markdown
# Document decision
## Why We Chose Not To Integrate TRELLIS
- Quality comparison: ...
- Speed comparison: ...
- Feature comparison: ...
- Conclusion: Hunyuan3D-2.1 + TripoSR cover our needs
```

---

### **Phase 4: Advanced Control (Week 4-5)** ⭐⭐⭐⭐

#### **4.1 Hunyuan3D-Omni Integration** (1 week)

**NEW File: `custom_workflows/omni_workflow.py`**
```python
#!/usr/bin/env python3
"""
Hunyuan3D-Omni Multi-Modal Control Workflow
Supports: Point Cloud, Bounding Box, Skeletal Pose, Voxel controls
"""

import torch
from pathlib import Path
from PIL import Image

class Hunyuan3DOmniWorkflow:
    """Multi-modal controlled 3D generation"""
    
    def __init__(self,
                 model_path='tencent/Hunyuan3D-Omni',
                 device='cuda'):
        """
        Initialize Omni workflow
        
        Args:
            model_path: Model path
            device: Device
        """
        self.device = device
        
        print("="*70)
        print("Initializing Hunyuan3D-Omni - MULTI-MODAL CONTROL")
        print("="*70)
        print("Supports: Point Cloud, BBox, Pose, Voxel controls")
        print("="*70)
        
        # Load Omni model (3.3B params)
        from hy3dgen.shapegen import Hunyuan3DOmniPipeline  # Hypothetical
        
        self.pipeline = Hunyuan3DOmniPipeline.from_pretrained(
            model_path,
            device=device
        )
        
        print("="*70)
        print("Initialization complete!")
        print("="*70)
    
    def process_with_control(self, 
                            image_path,
                            control_type='none',
                            control_data=None,
                            output_dir='outputs'):
        """
        Process with multi-modal control
        
        Args:
            image_path: Input image
            control_type: 'point', 'bbox', 'pose', 'voxel', 'none'
            control_data: Control-specific data
            output_dir: Output directory
            
        Returns:
            Dict with outputs
        """
        image = Image.open(image_path)
        
        # Generate with control
        print(f"Generating with {control_type} control...")
        output = self.pipeline(
            image=image,
            control_type=control_type,
            control_data=control_data
        )
        
        # Export
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        glb_path = output_dir / "model.glb"
        output.export(str(glb_path))
        
        return {
            'glb': str(glb_path),
            'control_type': control_type
        }
```

**GUI Integration:**
```python
# NEW Tab in GUI
with gr.Tab("🎮 Advanced Control (Omni)"):
    gr.Markdown("""
    Multi-modal control for precise 3D generation.
    Control geometry, pose, and dimensions.
    """)
    
    with gr.Row():
        with gr.Column():
            control_image = gr.Image(label="Input Image")
            
            control_type = gr.Radio(
                choices=[
                    'none',
                    'point',  # Point cloud
                    'bbox',   # Bounding box
                    'pose',   # Skeletal pose
                    'voxel'   # Voxel grid
                ],
                value='none',
                label="Control Type"
            )
            
            # Dynamic control inputs
            with gr.Group(visible=False) as point_control:
                point_file = gr.File(label="Point Cloud (.ply)")
                point_density = gr.Slider(100, 10000, value=1000,
                                         label="Point Density")
            
            with gr.Group(visible=False) as bbox_control:
                bbox_width = gr.Slider(0.5, 5.0, value=2.0, label="Width (m)")
                bbox_height = gr.Slider(0.5, 5.0, value=3.0, label="Height (m)")
                bbox_depth = gr.Slider(0.5, 5.0, value=1.5, label="Depth (m)")
            
            with gr.Group(visible=False) as pose_control:
                pose_file = gr.File(label="Pose Skeleton (.json)")
                pose_preset = gr.Dropdown(
                    choices=['T-pose', 'A-pose', 'Sitting', 'Running'],
                    label="Pose Preset"
                )
            
            with gr.Group(visible=False) as voxel_control:
                voxel_file = gr.File(label="Voxel Grid (.binvox)")
                voxel_resolution = gr.Slider(16, 128, value=64,
                                            label="Resolution")
            
            control_btn = gr.Button("🚀 Generate with Control")
        
        with gr.Column():
            control_output = gr.Model3D(label="Generated Model")
            control_status = gr.Textbox(label="Status")
    
    # Show/hide control inputs based on selection
    def update_control_visibility(control_type):
        return {
            point_control: gr.update(visible=(control_type == 'point')),
            bbox_control: gr.update(visible=(control_type == 'bbox')),
            pose_control: gr.update(visible=(control_type == 'pose')),
            voxel_control: gr.update(visible=(control_type == 'voxel'))
        }
    
    control_type.change(
        fn=update_control_visibility,
        inputs=[control_type],
        outputs=[point_control, bbox_control, pose_control, voxel_control]
    )
```

---

### **Phase 5: Part Editing (Week 6-7)** ⭐⭐⭐⭐

#### **5.1 Hunyuan3D-Part Integration** (1 week)

**NEW File: `custom_workflows/part_workflow.py`**
```python
#!/usr/bin/env python3
"""
Hunyuan3D-Part Segmentation Workflow
Auto-segment meshes into semantic parts
Uses P3-SAM + X-Part
"""

import torch
from pathlib import Path
import trimesh

class Hunyuan3DPartWorkflow:
    """Part-based segmentation and generation"""
    
    def __init__(self,
                 model_path='tencent/Hunyuan3D-Part',
                 device='cuda'):
        """
        Initialize Part workflow
        
        Args:
            model_path: Model path
            device: Device
        """
        self.device = device
        
        print("="*70)
        print("Initializing Hunyuan3D-Part - SEMANTIC SEGMENTATION")
        print("="*70)
        print("P3-SAM: 3D part detection")
        print("X-Part: Structure-coherent decomposition")
        print("="*70)
        
        # Load P3-SAM (part detection)
        from hy3dgen.part import P3SAM, XPart  # Hypothetical
        
        self.p3sam = P3SAM.from_pretrained(
            model_path,
            subfolder='p3sam',
            device=device
        )
        
        # Load X-Part (part generation)
        self.xpart = XPart.from_pretrained(
            model_path,
            subfolder='xpart',
            device=device
        )
        
        print("="*70)
        print("Initialization complete!")
        print("="*70)
    
    def segment_mesh(self, mesh_path, output_dir='outputs'):
        """
        Segment mesh into semantic parts
        
        Args:
            mesh_path: Input mesh (.glb or .obj)
            output_dir: Output directory
            
        Returns:
            Dict with part meshes and metadata
        """
        # Load mesh
        mesh = trimesh.load(mesh_path)
        
        # Stage 1: Detect parts with P3-SAM
        print("Detecting parts with P3-SAM...")
        part_segments = self.p3sam(mesh)
        # Returns: {'head': mask, 'body': mask, 'legs': [mask1, mask2], ...}
        
        # Stage 2: Generate complete parts with X-Part
        print("Generating complete parts with X-Part...")
        part_meshes = {}
        
        for part_name, mask in part_segments.items():
            part_mesh = self.xpart.complete_part(
                mesh,
                mask=mask,
                part_type=part_name
            )
            part_meshes[part_name] = part_mesh
        
        # Export parts
        output_dir = Path(output_dir) / "parts"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exported = {}
        for part_name, part_mesh in part_meshes.items():
            part_path = output_dir / f"{part_name}.obj"
            part_mesh.export(str(part_path))
            exported[part_name] = str(part_path)
        
        # Export metadata
        metadata = {
            'parts': list(part_meshes.keys()),
            'files': exported,
            'hierarchy': self._build_hierarchy(part_segments)
        }
        
        import json
        metadata_path = output_dir / "parts_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            'parts': part_meshes,
            'metadata': metadata,
            'metadata_path': str(metadata_path)
        }
    
    def _build_hierarchy(self, segments):
        """Build part hierarchy"""
        # Organize parts into hierarchical structure
        hierarchy = {
            'root': list(segments.keys())
        }
        return hierarchy
```

**GUI Integration:**
```python
# NEW Tab
with gr.Tab("🧩 Part Segmentation"):
    gr.Markdown("""
    Automatically segment 3D models into editable parts.
    Upload an existing model or generate a new one first.
    """)
    
    with gr.Row():
        with gr.Column():
            part_input_mesh = gr.File(
                label="Input Mesh (.glb or .obj)",
                file_types=['.glb', '.obj']
            )
            
            # Or generate new
            part_input_image = gr.Image(label="Or Generate New Model")
            part_generate_btn = gr.Button("Generate → Segment")
            
            # Segmentation button
            part_segment_btn = gr.Button("🧩 Segment into Parts", variant="primary")
        
        with gr.Column():
            # Part viewer
            part_preview = gr.Model3D(label="Segmented Model")
            
            # Part list
            part_list = gr.JSON(label="Detected Parts")
            
            # Download individual parts
            part_downloads = gr.File(
                label="Download Parts (.zip)",
                type="filepath"
            )
            
            part_status = gr.Textbox(label="Status")
    
    # Processing function
    def process_part_segmentation(mesh_file, progress=gr.Progress()):
        progress(0.2, desc="Loading mesh...")
        
        workflow = Hunyuan3DPartWorkflow()
        
        progress(0.4, desc="Detecting parts with P3-SAM...")
        progress(0.7, desc="Generating complete parts with X-Part...")
        
        results = workflow.segment_mesh(mesh_file.name)
        
        # Create zip of parts
        import zipfile
        zip_path = Path(results['metadata_path']).parent / "parts.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            for part_file in results['metadata']['files'].values():
                zf.write(part_file, Path(part_file).name)
        
        return (
            results['parts'][list(results['parts'].keys())[0]],  # Preview first part
            results['metadata'],
            str(zip_path),
            f"✅ Segmented into {len(results['parts'])} parts"
        )
    
    part_segment_btn.click(
        fn=process_part_segmentation,
        inputs=[part_input_mesh],
        outputs=[part_preview, part_list, part_downloads, part_status]
    )
```

---

### **Phase 6: Optional Advanced (Week 8+)**

#### **6.1 InstantMesh Auto Multi-View** (1 week)

**NEW File: `custom_workflows/instantmesh_workflow.py`**
```python
#!/usr/bin/env python3
"""
InstantMesh Auto Multi-View Generation
Generates consistent views from single image
"""

class InstantMeshWorkflow:
    """Auto multi-view generation"""
    
    def __init__(self,
                 model_path='TencentARC/InstantMesh',
                 device='cuda'):
        """Initialize InstantMesh"""
        from instant_mesh import InstantMeshPipeline  # Hypothetical
        
        self.pipeline = InstantMeshPipeline.from_pretrained(
            model_path,
            device=device
        )
    
    def generate_multiview(self, image_path):
        """
        Generate 4 consistent views from single image
        
        Args:
            image_path: Single input image
            
        Returns:
            Dict with front/back/left/right views
        """
        from PIL import Image
        
        image = Image.open(image_path)
        
        # Generate views
        views = self.pipeline.generate_views(image)
        # Returns: {'front': img, 'back': img, 'left': img, 'right': img}
        
        return views
```

**GUI Integration:**
```python
# Update Multiview tab
with gr.Tab("📐 Multiview"):
    # Add checkbox
    auto_generate_views = gr.Checkbox(
        label="Auto-generate missing views (InstantMesh)",
        value=False,
        info="Generate consistent views from front view only"
    )
    
    # If enabled, only require front view
    # Auto-generate back, left, right
```

---

## 📊 **Implementation Timeline Summary**

```
Week 1: Foundation
├─ Day 1-2: Hunyuan3D-2.1 upgrade (2h) + Testing (1d)
├─ Day 3: Benchmark infrastructure
└─ Day 4-5: TRELLIS evaluation

Week 2: Speed Layer  
├─ Day 1-3: TripoSR integration
└─ Day 4-5: GUI quality presets

Week 3: TRELLIS Decision
├─ If good: 5 days integration
└─ If skip: Planning next phases

Week 4-5: Advanced Control
└─ Hunyuan3D-Omni (5 days) + GUI (2 days)

Week 6-7: Part Editing
└─ Hunyuan3D-Part (5 days) + GUI (2 days)

Week 8+: Optional
└─ InstantMesh, polish, optimization
```

---

## 🔧 **Technical Requirements**

### **Dependencies to Add:**

**`requirements.txt`:**
```txt
# Existing...

# NEW: Model integrations
triposr>=0.1.0              # TripoSR ultra-fast
# trellis-3d>=0.1.0         # TRELLIS (if integrated after testing)

# UPDATED: Hunyuan3D models (no new deps, just model paths)
```

### **VRAM Requirements:**

| Model | Minimum | Recommended | Notes |
|-------|---------|-------------|-------|
| Hunyuan3D-2.1 | 16GB | 24GB | Same as 2.0 |
| TripoSR | **4GB** | 8GB | Very efficient! |
| TRELLIS | TBD | TBD | Test in Phase 1 |
| Hunyuan3D-Omni | **10GB** | 16GB | Lower than base |
| Hunyuan3D-Part | 12GB | 16GB | Two-stage |
| InstantMesh | 8GB | 12GB | Multi-view |

---

## ✅ **Success Criteria**

### **After 8 Weeks:**

**✅ Models Available:**
- Hunyuan3D-2.1 (PBR materials)
- TripoSR (0.5s draft)
- TRELLIS (if testing successful)
- Hunyuan3D-Omni (advanced control)
- Hunyuan3D-Part (part editing)

**✅ Workflow Options:**
```
1. Draft (0.5s) → TripoSR
2. Preview (30s) → Mini
3. Balanced (2min) → H3D-2.1
4. Quality (5min) → H3D-2.1 Max
5. Control (2min) → Omni
6. Edit Parts → Part
```

**✅ GUI Features:**
- Quality preset selector
- Advanced model selection
- PBR material export
- Multi-modal control tab
- Part segmentation tab
- Benchmark/comparison tools

**✅ Documentation:**
- Model comparison guide
- Usage tutorials
- API documentation
- Troubleshooting guide

---

## 🎯 **Testing & Validation**

### **Test Plan for Each Model:**

```python
class ModelIntegrationTest:
    def test_model_loading(self):
        """Model loads without errors"""
        workflow = NewModelWorkflow()
        assert workflow.pipeline is not None
    
    def test_single_image_generation(self):
        """Generates valid output"""
        workflow = NewModelWorkflow()
        result = workflow.process_single_image('test.jpg')
        assert result['glb'].exists()
    
    def test_vram_usage(self):
        """VRAM within expected limits"""
        workflow = NewModelWorkflow()
        peak_vram = measure_vram(workflow.process_single_image, 'test.jpg')
        assert peak_vram < expected_max_vram
    
    def test_generation_speed(self):
        """Speed meets expectations"""
        workflow = NewModelWorkflow()
        elapsed = measure_time(workflow.process_single_image, 'test.jpg')
        assert elapsed < expected_max_time
    
    def test_output_quality(self):
        """Output has required attributes"""
        workflow = NewModelWorkflow()
        result = workflow.process_single_image('test.jpg')
        mesh = load_mesh(result['glb'])
        assert mesh.vertices.shape[0] > 1000
        assert mesh.faces.shape[0] > 1000
```

---

## 📚 **Documentation to Create**

1. **`MODEL_COMPARISON.md`** - Detailed benchmark results
2. **`USAGE_GUIDE.md`** - How to use each model
3. **`API_REFERENCE.md`** - Developer documentation
4. **`TROUBLESHOOTING.md`** - Common issues and fixes
5. **`CHANGELOG.md`** - Version history and updates

---

## 🚀 **Next Steps**

### **Immediate Actions:**

1. **✅ Review this plan** with stakeholders
2. **✅ Approve Phase 1** (Foundation - Week 1)
3. **✅ Set up development environment**
4. **✅ Create feature branch**: `feature/multi-model-integration`
5. **✅ Begin Phase 1.1**: Hunyuan3D-2.1 upgrade

### **Before Starting:**

- [ ] Backup current working version
- [ ] Create test image dataset (10-20 images)
- [ ] Set up VRAM monitoring tools
- [ ] Create benchmarking scripts
- [ ] Document current performance baseline

---

## 💡 **Risk Mitigation**

### **Risks & Mitigation:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| TRELLIS is slower than expected | Medium | Skip integration, focus on H3D ecosystem |
| VRAM requirements too high | High | Implement model quantization, add CPU fallback |
| API changes in HuggingFace models | Medium | Pin specific model versions in requirements |
| Integration breaks existing workflows | High | Comprehensive testing, maintain backward compatibility |
| User confusion with many options | Medium | Clear UI, quality presets, good documentation |

---

## 🎓 **Lessons from Architecture Analysis**

1. **Consistent API Pattern**: All models use `from_pretrained()` - easy to extend
2. **Lazy Loading**: GUI initializes models on first use - efficient
3. **Modular Workflows**: Each workflow is independent - easy to add new ones
4. **Configuration-Driven**: YAML config allows user customization
5. **Gradio Flexibility**: Easy to add new tabs and controls

---

## ✨ **Expected Outcome**

After 8 weeks:

**🏆 Most Advanced Open-Source 3D Generation GUI**

**Features:**
- ✅ 5-6 model options
- ✅ 0.5s to 5min generation times
- ✅ PBR materials for game engines
- ✅ Multi-modal controls
- ✅ Part-based editing
- ✅ Comprehensive testing/benchmarking

**User Experience:**
```
1. User uploads image
2. Selects quality preset:
   - Draft (0.5s) for quick iteration
   - Quality (2min) for final asset
3. Optional: Adds controls (pose, bbox, etc.)
4. Generates 3D model
5. Optional: Segments into editable parts
6. Exports with PBR materials
7. Direct import to Unity/Unreal
```

**Result**: **Professional 3D asset generation pipeline from image to game engine in minutes!** 🚀

---

**Status**: Ready for implementation  
**Next**: Begin Phase 1.1 - Hunyuan3D-2.1 Upgrade  
**Timeline**: 8-10 weeks to completion  
**Confidence**: High (based on thorough architecture analysis)

**Date**: November 2, 2025  
**Version**: 1.0 - Master Implementation Plan

