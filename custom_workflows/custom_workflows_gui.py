#!/usr/bin/env python3
"""
Custom Workflows GUI
====================

Comprehensive Gradio interface for all Hunyuan3D-2 custom workflows.

Features:
- Complete workflow (single image with enhancements)
- Multiview workflow (front/back/left/right views)
- Batch processing (multiple images)
- Texture extraction (from existing models)
- Full configuration UI with all settings
- Export format selection (GLB, OBJ, separate PNG)

Usage:
    python custom_workflows_gui.py
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gradio as gr
import torch
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import workflow classes
from complete_workflow import Hunyuan3DCompleteWorkflow
from multiview_workflow import Hunyuan3DMultiviewWorkflow
from extract_texture import extract_texture_from_mesh


class WorkflowConfig:
    """Manages workflow configuration from YAML"""
    
    def __init__(self, config_path='workflow_config.yaml'):
        self.config_path = Path(__file__).parent / config_path
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Load configuration from YAML file"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self.get_default_config()
    
    def save_config(self, config: dict):
        """Save configuration to YAML file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        self.config = config
    
    def get_default_config(self) -> dict:
        """Return default configuration"""
        return {
            'model': {
                'type': 'h2',
                'device': 'cuda',
                'enable_flashvdm': True
            },
            'face_processing': {
                'enabled': True,
                'auto_detect': True,
                'confidence_threshold': 0.5,
                'face_padding': 0.3
            },
            'image_enhancement': {
                'enabled': True,
                'sharpness_factor': 1.5,
                'normalize_illumination': True,
                'perspective_correction': False,
                'rotation_angle': 0.0
            },
            'generation': {
                'num_inference_steps': 50,
                'guidance_scale': 7.5,
                'octree_resolution': 384,
                'num_chunks': 20000,
                'seed': 12345
            },
            'texture': {
                'enabled': True,
                'target_face_count': 50000,
                'render_size': 2048,
                'texture_size': 2048
            },
            'export': {
                'formats': ['glb', 'obj'],
                'extract_texture': True,
                'include_normals': True
            },
            'batch': {
                'skip_existing': True,
                'continue_on_error': True,
                'max_workers': 1
            },
            'output': {
                'directory': 'outputs',
                'organize_by_date': False,
                'save_intermediate': False,
                'naming_pattern': '{name}_textured'
            }
        }


class CustomWorkflowsGUI:
    """Main GUI application"""
    
    def __init__(self):
        self.config_manager = WorkflowConfig()
        self.config = self.config_manager.config
        self.workflow_single = None
        self.workflow_multiview = None
        
        # Check for optional dependencies
        self.facexlib_available = self._check_facexlib()
        self.kornia_available = self._check_kornia()
    
    def _check_facexlib(self):
        """Check if facexlib is available"""
        try:
            import facexlib
            return True
        except ImportError:
            return False
    
    def _check_kornia(self):
        """Check if kornia is available"""
        try:
            import kornia
            return True
        except ImportError:
            return False
    
    def initialize_workflow_single(self, model_type: str, device: str, 
                                   enable_face: bool, enable_enhance: bool,
                                   enable_flashvdm: bool,
                                   octree_res: int, steps: int, guidance: float):
        """Initialize or update single image workflow"""
        model_path = 'tencent/Hunyuan3D-2' if model_type == 'h2' else 'tencent/Hunyuan3D-2mini'
        
        # Check if optional features are available
        actual_enable_face = enable_face and self.facexlib_available
        actual_enable_enhance = enable_enhance and self.kornia_available
        
        # Build status message
        status_msgs = ["✅ Model loaded successfully!"]
        
        if enable_face and not self.facexlib_available:
            status_msgs.append("⚠️ Face processing disabled: facexlib not installed")
            status_msgs.append("   Install with: uv pip install facexlib")
        
        if enable_enhance and not self.kornia_available:
            status_msgs.append("⚠️ Image enhancement disabled: kornia not installed")
            status_msgs.append("   Install with: uv pip install kornia")
        
        self.workflow_single = Hunyuan3DCompleteWorkflow(
            model_path=model_path,
            device=device,
            enable_face_processing=actual_enable_face,
            enable_image_enhancement=actual_enable_enhance,
            enable_flashvdm=enable_flashvdm,
            octree_resolution=octree_res,
            num_inference_steps=steps,
            guidance_scale=guidance
        )
        
        return "\n".join(status_msgs)
    
    def process_single_image(self, image, is_portrait: bool, output_dir: str,
                            model_type: str, device: str,
                            enable_face: bool, enable_enhance: bool, enable_flashvdm: bool,
                            octree_res: int, steps: int, guidance: float,
                            export_glb: bool, export_obj: bool, extract_tex: bool,
                            progress=gr.Progress()) -> Tuple[str, str, str, str]:
        """Process single image through complete workflow"""
        if image is None:
            return None, None, None, "❌ Please upload an image"
        
        try:
            progress(0.1, desc="Initializing model...")
            
            # Initialize workflow if needed
            if self.workflow_single is None:
                status = self.initialize_workflow_single(
                    model_type, device, enable_face, enable_enhance, enable_flashvdm,
                    octree_res, steps, guidance
                )
            
            # Save uploaded image temporarily
            progress(0.2, desc="Preprocessing image...")
            temp_dir = Path(output_dir) / "temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_image_path = temp_dir / "input.png"
            image.save(temp_image_path)
            
            # Process image
            progress(0.3, desc="Generating 3D model...")
            results = self.workflow_single.process_single_image(
                str(temp_image_path),
                output_dir=output_dir,
                is_portrait=is_portrait
            )
            
            progress(0.9, desc="Preparing results...")
            
            # Prepare output files based on export settings
            glb_file = results.get('glb') if export_glb else None
            obj_file = results.get('obj') if export_obj else None
            texture_file = results.get('texture') if extract_tex else None
            
            # Load texture image for preview
            texture_preview = None
            if texture_file and Path(texture_file).exists():
                texture_preview = Image.open(texture_file)
            
            status = "✅ Processing complete!"
            progress(1.0, desc="Done!")
            
            return glb_file, obj_file, texture_preview, status
            
        except Exception as e:
            import traceback
            error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
            return None, None, None, error_msg
    
    def process_multiview(self, front_img, back_img, left_img, right_img,
                         output_dir: str, output_name: str,
                         device: str, enable_face: bool, enable_enhance: bool,
                         turbo: bool, enable_flashvdm: bool,
                         export_glb: bool, export_obj: bool, extract_tex: bool,
                         progress=gr.Progress()) -> Tuple[str, str, str, str]:
        """Process multiview images"""
        # Collect provided views
        views = {}
        if front_img is not None:
            views['front'] = front_img
        if back_img is not None:
            views['back'] = back_img
        if left_img is not None:
            views['left'] = left_img
        if right_img is not None:
            views['right'] = right_img
        
        if not views:
            return None, None, None, "❌ Please provide at least one view"
        
        try:
            progress(0.1, desc="Initializing multiview model...")
            
            # Check if optional features are available
            actual_enable_face = enable_face and self.facexlib_available
            actual_enable_enhance = enable_enhance and self.kornia_available
            
            # Initialize workflow
            subfolder = 'hunyuan3d-dit-v2-mv-turbo' if turbo else 'hunyuan3d-dit-v2-mv'
            workflow_mv = Hunyuan3DMultiviewWorkflow(
                model_path='tencent/Hunyuan3D-2mv',
                subfolder=subfolder,
                device=device,
                enable_face_processing=actual_enable_face,
                enable_image_enhancement=actual_enable_enhance,
                enable_flashvdm=enable_flashvdm
            )
            
            progress(0.3, desc="Processing views...")
            results = workflow_mv.process_views(
                views,
                output_dir=output_dir,
                output_name=output_name
            )
            
            progress(0.9, desc="Preparing results...")
            
            # Prepare output files
            glb_file = results.get('glb') if export_glb else None
            obj_file = results.get('obj') if export_obj else None
            texture_file = results.get('texture') if extract_tex else None
            
            texture_preview = None
            if texture_file and Path(texture_file).exists():
                texture_preview = Image.open(texture_file)
            
            status = f"✅ Multiview processing complete! Used {len(views)} views."
            progress(1.0, desc="Done!")
            
            return glb_file, obj_file, texture_preview, status
            
        except Exception as e:
            import traceback
            error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
            return None, None, None, error_msg
    
    def process_batch(self, images: List, is_portrait: bool, output_dir: str,
                     model_type: str, device: str,
                     enable_face: bool, enable_enhance: bool, enable_flashvdm: bool,
                     octree_res: int, steps: int, guidance: float,
                     skip_existing: bool,
                     export_glb: bool, export_obj: bool, extract_tex: bool,
                     progress=gr.Progress()) -> Tuple[List[str], str]:
        """Process multiple images in batch"""
        if not images or len(images) == 0:
            return [], "❌ Please upload at least one image"
        
        try:
            progress(0.05, desc="Initializing model...")
            
            # Initialize workflow
            if self.workflow_single is None:
                self.initialize_workflow_single(
                    model_type, device, enable_face, enable_enhance, enable_flashvdm,
                    octree_res, steps, guidance
                )
            
            results_gallery = []
            success_count = 0
            failed = []
            
            for idx, img in enumerate(images):
                progress((idx + 1) / len(images), 
                        desc=f"Processing image {idx + 1}/{len(images)}...")
                
                try:
                    # Save temp image
                    temp_dir = Path(output_dir) / "temp"
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    temp_path = temp_dir / f"batch_{idx}.png"
                    img.save(temp_path)
                    
                    # Check if output exists
                    output_glb = Path(output_dir) / f"batch_{idx}_textured.glb"
                    if skip_existing and output_glb.exists():
                        print(f"⏭️  Skipping {idx} (already exists)")
                        continue
                    
                    # Process
                    result = self.workflow_single.process_single_image(
                        str(temp_path),
                        output_dir=output_dir,
                        is_portrait=is_portrait
                    )
                    
                    # Add texture preview to gallery
                    if extract_tex and result.get('texture'):
                        tex_path = result['texture']
                        if Path(tex_path).exists():
                            results_gallery.append(tex_path)
                    
                    success_count += 1
                    
                except Exception as e:
                    failed.append(f"Image {idx}: {str(e)}")
                    print(f"❌ Error processing image {idx}: {e}")
            
            status = f"✅ Batch complete! Processed {success_count}/{len(images)} images"
            if failed:
                status += f"\n\n❌ Failed ({len(failed)}):\n" + "\n".join(failed)
            
            progress(1.0, desc="Batch complete!")
            return results_gallery, status
            
        except Exception as e:
            import traceback
            error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
            return [], error_msg
    
    def extract_texture(self, mesh_file, output_path: Optional[str] = None,
                       progress=gr.Progress()) -> Tuple[str, str, str]:
        """Extract texture from mesh file"""
        if mesh_file is None:
            return None, None, "❌ Please upload a mesh file"
        
        try:
            progress(0.3, desc="Loading mesh...")
            
            # Save uploaded file
            temp_mesh = Path("temp_mesh.glb")
            temp_mesh.write_bytes(mesh_file)
            
            progress(0.6, desc="Extracting texture...")
            
            # Extract texture
            if output_path is None:
                output_path = "extracted_texture.png"
            
            texture_path = extract_texture_from_mesh(str(temp_mesh), output_path)
            
            if texture_path and Path(texture_path).exists():
                texture_preview = Image.open(texture_path)
                status = f"✅ Texture extracted successfully!\nSize: {texture_preview.size}"
                progress(1.0, desc="Done!")
                return texture_path, texture_preview, status
            else:
                return None, None, "❌ No texture found in mesh file"
                
        except Exception as e:
            import traceback
            error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
            return None, None, error_msg
        finally:
            # Cleanup
            if temp_mesh.exists():
                temp_mesh.unlink()
    
    def create_ui(self):
        """Create Gradio UI"""
        with gr.Blocks(title="Hunyuan3D-2 Custom Workflows", theme=gr.themes.Soft()) as demo:
            # Build dependency status message
            dep_status = []
            if not self.facexlib_available:
                dep_status.append("⚠️ **facexlib** not installed - Face processing disabled")
            if not self.kornia_available:
                dep_status.append("⚠️ **kornia** not installed - Image enhancement disabled")
            
            dep_msg = ""
            if dep_status:
                dep_msg = "\n\n**⚠️ Missing Required Dependencies:**\n\n"
                dep_msg += "\n\n".join(dep_status)
                dep_msg += "\n\n**Install now:** `uv pip install facexlib kornia`"
                dep_msg += "\n\nThese packages are required for full functionality."
            
            gr.Markdown(f"""
            # 🎨 Hunyuan3D-2 Custom Workflows
            
            High-quality 3D generation with face processing, image enhancement, and texture extraction.
            {dep_msg}
            """)
            
            # Settings section (collapsible)
            with gr.Accordion("⚙️ Global Settings", open=False):
                with gr.Row():
                    with gr.Column():
                        model_type = gr.Radio(
                            choices=['h2', 'mini'],
                            value=self.config['model']['type'],
                            label="Model",
                            info="h2: Full 2.6B (best quality), mini: 0.6B (faster)"
                        )
                        device = gr.Radio(
                            choices=['cuda', 'cpu'],
                            value=self.config['model']['device'],
                            label="Device"
                        )
                        enable_flashvdm = gr.Checkbox(
                            value=self.config['model']['enable_flashvdm'],
                            label="Enable Flash VDM (faster generation)"
                        )
                    
                    with gr.Column():
                        # Check availability and show warnings
                        face_label = "Enable Face Processing"
                        enhance_label = "Enable Image Enhancement"
                        
                        if not self.facexlib_available:
                            face_label += " ⚠️ (facexlib not installed)"
                        
                        if not self.kornia_available:
                            enhance_label += " ⚠️ (kornia not installed)"
                        
                        enable_face = gr.Checkbox(
                            value=self.config['face_processing']['enabled'] and self.facexlib_available,
                            label=face_label,
                            info="Auto-detect and align faces (requires facexlib)" if not self.facexlib_available else None,
                            interactive=self.facexlib_available
                        )
                        enable_enhance = gr.Checkbox(
                            value=self.config['image_enhancement']['enabled'] and self.kornia_available,
                            label=enhance_label,
                            info="Sharpening and illumination (requires kornia)" if not self.kornia_available else None,
                            interactive=self.kornia_available
                        )
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Generation Settings")
                        num_steps = gr.Slider(
                            minimum=20, maximum=100, step=5,
                            value=self.config['generation']['num_inference_steps'],
                            label="Inference Steps",
                            info="More steps = higher quality, slower"
                        )
                        guidance_scale = gr.Slider(
                            minimum=1.0, maximum=15.0, step=0.5,
                            value=self.config['generation']['guidance_scale'],
                            label="Guidance Scale"
                        )
                        octree_res = gr.Slider(
                            minimum=128, maximum=512, step=64,
                            value=self.config['generation']['octree_resolution'],
                            label="Octree Resolution",
                            info="Higher = more detail, more VRAM"
                        )
                    
                    with gr.Column():
                        gr.Markdown("### Export Settings")
                        export_glb = gr.Checkbox(
                            value='glb' in self.config['export']['formats'],
                            label="Export GLB"
                        )
                        export_obj = gr.Checkbox(
                            value='obj' in self.config['export']['formats'],
                            label="Export OBJ (with MTL)"
                        )
                        extract_texture_png = gr.Checkbox(
                            value=self.config['export']['extract_texture'],
                            label="Extract Texture as Separate PNG"
                        )
            
            # Workflow tabs
            with gr.Tabs():
                # Tab 1: Complete Workflow (Single Image)
                with gr.Tab("🖼️ Single Image"):
                    gr.Markdown("""
                    Process a single image through the complete pipeline with all enhancements.
                    Best for portraits and detailed objects.
                    """)
                    
                    with gr.Row():
                        with gr.Column():
                            single_image = gr.Image(
                                label="Input Image",
                                type="pil",
                                height=400
                            )
                            single_portrait = gr.Checkbox(
                                label="Portrait Mode (auto face detection & alignment)",
                                value=False
                            )
                            single_output_dir = gr.Textbox(
                                label="Output Directory",
                                value=self.config['output']['directory']
                            )
                            single_btn = gr.Button("🚀 Generate 3D Model", variant="primary", size="lg")
                        
                        with gr.Column():
                            single_glb = gr.File(label="GLB Output")
                            single_obj = gr.File(label="OBJ Output")
                            single_texture = gr.Image(label="Texture Preview", type="pil")
                            single_status = gr.Textbox(label="Status", lines=5)
                    
                    single_btn.click(
                        fn=self.process_single_image,
                        inputs=[
                            single_image, single_portrait, single_output_dir,
                            model_type, device, enable_face, enable_enhance, enable_flashvdm,
                            octree_res, num_steps, guidance_scale,
                            export_glb, export_obj, extract_texture_png
                        ],
                        outputs=[single_glb, single_obj, single_texture, single_status]
                    )
                
                # Tab 2: Multiview Workflow
                with gr.Tab("📐 Multiview"):
                    gr.Markdown("""
                    Generate 3D models from multiple views (front, back, left, right).
                    Provide at least one view, more views = better quality.
                    """)
                    
                    with gr.Row():
                        with gr.Column():
                            mv_front = gr.Image(label="Front View", type="pil", height=250)
                            mv_back = gr.Image(label="Back View", type="pil", height=250)
                        with gr.Column():
                            mv_left = gr.Image(label="Left View", type="pil", height=250)
                            mv_right = gr.Image(label="Right View", type="pil", height=250)
                    
                    with gr.Row():
                        mv_output_dir = gr.Textbox(
                            label="Output Directory",
                            value=self.config['output']['directory']
                        )
                        mv_output_name = gr.Textbox(
                            label="Output Name",
                            value="multiview"
                        )
                        mv_turbo = gr.Checkbox(
                            label="Use Turbo Model (faster, lower quality)",
                            value=False
                        )
                    
                    mv_btn = gr.Button("🚀 Generate from Multiview", variant="primary", size="lg")
                    
                    with gr.Row():
                        mv_glb = gr.File(label="GLB Output")
                        mv_obj = gr.File(label="OBJ Output")
                        mv_texture = gr.Image(label="Texture Preview", type="pil")
                    
                    mv_status = gr.Textbox(label="Status", lines=3)
                    
                    mv_btn.click(
                        fn=self.process_multiview,
                        inputs=[
                            mv_front, mv_back, mv_left, mv_right,
                            mv_output_dir, mv_output_name,
                            device, enable_face, enable_enhance, mv_turbo, enable_flashvdm,
                            export_glb, export_obj, extract_texture_png
                        ],
                        outputs=[mv_glb, mv_obj, mv_texture, mv_status]
                    )
                
                # Tab 3: Batch Processing
                with gr.Tab("📦 Batch Processing"):
                    gr.Markdown("""
                    Process multiple images at once. All images will be processed with the same settings.
                    """)
                    
                    with gr.Row():
                        with gr.Column():
                            batch_images = gr.File(
                                label="Upload Images",
                                file_count="multiple",
                                file_types=["image"]
                            )
                            batch_portrait = gr.Checkbox(
                                label="Process as Portraits",
                                value=False
                            )
                            batch_output_dir = gr.Textbox(
                                label="Output Directory",
                                value="batch_outputs"
                            )
                            batch_skip_existing = gr.Checkbox(
                                label="Skip Existing Outputs",
                                value=self.config['batch']['skip_existing']
                            )
                            batch_btn = gr.Button("🚀 Process Batch", variant="primary", size="lg")
                        
                        with gr.Column():
                            batch_gallery = gr.Gallery(
                                label="Generated Textures",
                                columns=3,
                                height=400
                            )
                            batch_status = gr.Textbox(label="Status", lines=8)
                    
                    # Note: Batch processing with file uploads requires conversion
                    def batch_wrapper(files, *args):
                        if not files:
                            return [], "❌ No files uploaded"
                        # Convert file paths to PIL images
                        images = []
                        for file in files:
                            try:
                                img = Image.open(file.name)
                                images.append(img)
                            except Exception as e:
                                print(f"Error loading {file.name}: {e}")
                        return self.process_batch(images, *args)
                    
                    batch_btn.click(
                        fn=batch_wrapper,
                        inputs=[
                            batch_images, batch_portrait, batch_output_dir,
                            model_type, device, enable_face, enable_enhance, enable_flashvdm,
                            octree_res, num_steps, guidance_scale,
                            batch_skip_existing,
                            export_glb, export_obj, extract_texture_png
                        ],
                        outputs=[batch_gallery, batch_status]
                    )
                
                # Tab 4: Texture Extraction
                with gr.Tab("🎨 Texture Extraction"):
                    gr.Markdown("""
                    Extract texture as a separate PNG file from existing GLB/OBJ models.
                    Useful for editing textures or using in other software.
                    """)
                    
                    with gr.Row():
                        with gr.Column():
                            tex_mesh_file = gr.File(
                                label="Upload Mesh File (GLB/OBJ)",
                                file_types=[".glb", ".obj"]
                            )
                            tex_output_path = gr.Textbox(
                                label="Output Path (optional)",
                                placeholder="extracted_texture.png"
                            )
                            tex_btn = gr.Button("🎨 Extract Texture", variant="primary", size="lg")
                        
                        with gr.Column():
                            tex_file = gr.File(label="Extracted Texture (PNG)")
                            tex_preview = gr.Image(label="Texture Preview", type="pil")
                            tex_status = gr.Textbox(label="Status", lines=3)
                    
                    tex_btn.click(
                        fn=self.extract_texture,
                        inputs=[tex_mesh_file, tex_output_path],
                        outputs=[tex_file, tex_preview, tex_status]
                    )
            
            # Footer
            gr.Markdown("""
            ---
            ### 📖 Tips
            - **Portrait Mode**: Enable for faces/portraits to auto-align and center
            - **Image Enhancement**: Sharpening and illumination normalization for better quality
            - **Octree Resolution**: 384 for high detail (requires 24GB+ VRAM), 256 for lower VRAM
            - **Inference Steps**: 50 for best quality, 30 for faster results
            - **Export Formats**: GLB for Blender/game engines, OBJ for traditional 3D software
            
            ### 💾 Output Files
            - `*_textured.glb`: Complete textured model in GLB format
            - `*_textured.obj` + `*_textured.mtl`: Textured model in OBJ format
            - `*_texture.png`: Separate texture map (2048x2048 by default)
            """)
        
        return demo


def main():
    """Launch GUI"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Custom Workflows GUI')
    parser.add_argument('--share', action='store_true', help='Create shareable link')
    parser.add_argument('--port', type=int, default=7860, help='Port to run on')
    parser.add_argument('--server', type=str, default='127.0.0.1', help='Server address')
    args = parser.parse_args()
    
    # Create and launch GUI
    print("="*70)
    print("Hunyuan3D-2 Custom Workflows GUI")
    print("="*70)
    print("\nInitializing interface...")
    
    app = CustomWorkflowsGUI()
    demo = app.create_ui()
    
    print("\nLaunching...")
    demo.launch(
        server_name=args.server,
        server_port=args.port,
        share=args.share,
        inbrowser=True
    )


if __name__ == "__main__":
    main()

