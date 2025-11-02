#!/usr/bin/env python3
"""
Multiview Hunyuan3D-2 Workflow
===============================

Process multiple views (front/back/left/right) to generate high-quality 3D models.

Usage:
    python multiview_workflow.py --front front.jpg --back back.jpg --left left.jpg
    python multiview_workflow.py front.jpg back.jpg left.jpg right.jpg  # Auto-detects order
"""

import argparse
import os
import sys
import time
from pathlib import Path

import torch
import trimesh
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Hunyuan3D imports
from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
from hy3dgen.texgen import Hunyuan3DPaintPipeline

# Custom tool imports
try:
    from hy3dgen.face_processor import FaceProcessor
    FACE_AVAILABLE = True
except ImportError:
    FACE_AVAILABLE = False

try:
    from hy3dgen.image_enhancer import ImageEnhancer
    KORNIA_AVAILABLE = True
except ImportError:
    KORNIA_AVAILABLE = False

from extract_texture import extract_texture_from_mesh


class Hunyuan3DMultiviewWorkflow:
    """Multiview 3D generation workflow"""
    
    def __init__(self,
                 model_path='tencent/Hunyuan3D-2mv',
                 subfolder='hunyuan3d-dit-v2-mv',
                 device='cuda',
                 enable_face_processing=True,
                 enable_image_enhancement=True,
                 enable_flashvdm=False):
        """
        Initialize multiview workflow.
        
        Args:
            model_path: Multiview model path
            subfolder: Model subfolder
            device: 'cuda' or 'cpu'
            enable_face_processing: Enable face detection
            enable_image_enhancement: Enable kornia enhancement
            enable_flashvdm: Enable flash VDM (experimental for multiview)
        """
        self.device = device
        self.enable_face = enable_face_processing and FACE_AVAILABLE
        self.enable_enhance = enable_image_enhancement and KORNIA_AVAILABLE
        
        print("="*70)
        print("Initializing Hunyuan3D-2 Multiview Workflow")
        print("="*70)
        
        # Initialize custom tools
        if self.enable_face:
            print("✓ Initializing face processor...")
            self.face_processor = FaceProcessor(device=device)
        
        if self.enable_enhance:
            print("✓ Initializing image enhancer...")
            self.enhancer = ImageEnhancer(device=device)
        
        print("✓ Initializing background remover...")
        self.rembg = BackgroundRemover()
        
        print(f"✓ Loading multiview shape model ({subfolder})...")
        self.pipeline_shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            model_path,
            subfolder=subfolder
        )
        
        if enable_flashvdm:
            print("✓ Enabling Flash VDM...")
            self.pipeline_shape.enable_flashvdm()
        
        print("✓ Loading texture generation model...")
        self.pipeline_tex = Hunyuan3DPaintPipeline.from_pretrained('tencent/Hunyuan3D-2')
        
        print("="*70)
        print("Initialization complete!")
        print("="*70)
        print()
    
    def process_views(self, views_dict, output_dir='outputs', output_name='multiview'):
        """
        Process multiple views through the pipeline.
        
        Args:
            views_dict: Dictionary with keys 'front', 'back', 'left', 'right'
                       and values as image paths or PIL Images
            output_dir: Output directory
            output_name: Base name for output files
            
        Returns:
            dict: Paths to generated files
        """
        start_time = time.time()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timing = {}
        
        print("\n" + "="*70)
        print(f"Processing {len(views_dict)} views")
        print("="*70)
        
        # Stage 1: Load and process each view
        print("\n[1/6] Loading and processing views...")
        t0 = time.time()
        
        processed_views = {}
        for view_name, view_input in views_dict.items():
            print(f"\n  Processing {view_name} view...")
            
            # Load image
            if isinstance(view_input, str):
                image = Image.open(view_input).convert("RGBA")
                print(f"    Loaded from: {Path(view_input).name}")
            else:
                image = view_input
            
            print(f"    Size: {image.size}")
            
            # Face processing (only for front view typically)
            if view_name == 'front' and self.enable_face:
                faces = self.face_processor.detect_faces(image)
                if len(faces) > 0:
                    print(f"    ✓ Detected {len(faces)} face(s)")
                    image = self.face_processor.center_on_face(image)
            
            # Image enhancement
            if self.enable_enhance:
                image = self.enhancer.enhance_for_3d(image, sharpen=True, normalize_illum=True)
                print(f"    ✓ Enhanced")
            
            # Background removal
            if image.mode == "RGB":
                image = self.rembg(image.convert('RGB'))
            print(f"    ✓ Background removed")
            
            processed_views[view_name] = image
        
        timing['preprocess'] = time.time() - t0
        print(f"\n  Total preprocessing time: {timing['preprocess']:.2f}s")
        
        # Stage 2: Generate 3D mesh from multiview
        print("\n[2/6] Generating 3D mesh from multiple views...")
        t0 = time.time()
        mesh = self.pipeline_shape(
            image=processed_views,
            num_inference_steps=50,
            octree_resolution=380,
            num_chunks=20000,
            generator=torch.manual_seed(12345),
            output_type='trimesh'
        )[0]
        timing['shape'] = time.time() - t0
        print(f"      ✓ Mesh generated ({timing['shape']:.2f}s)")
        print(f"      Faces: {len(mesh.faces):,}, Vertices: {len(mesh.vertices):,}")
        
        # Stage 3: Generate texture (using front view)
        print("\n[3/6] Generating texture...")
        t0 = time.time()
        reference_view = processed_views.get('front', list(processed_views.values())[0])
        textured_mesh = self.pipeline_tex(mesh, image=reference_view)
        timing['texture'] = time.time() - t0
        print(f"      ✓ Texture generated ({timing['texture']:.2f}s)")
        
        # Stage 4: Export files
        print("\n[4/6] Exporting files...")
        t0 = time.time()
        
        results = {}
        
        # Export GLB
        glb_path = output_dir / f"{output_name}_textured.glb"
        textured_mesh.export(str(glb_path))
        results['glb'] = str(glb_path)
        print(f"      ✓ Exported GLB: {glb_path.name}")
        
        # Export OBJ
        obj_path = output_dir / f"{output_name}_textured.obj"
        textured_mesh.export(str(obj_path))
        results['obj'] = str(obj_path)
        print(f"      ✓ Exported OBJ: {obj_path.name}")
        
        # Extract texture
        texture_path = extract_texture_from_mesh(str(glb_path),
                                                 str(output_dir / f"{output_name}_texture.png"))
        if texture_path:
            results['texture'] = texture_path
            print(f"      ✓ Extracted texture: {Path(texture_path).name}")
        
        timing['export'] = time.time() - t0
        timing['total'] = time.time() - start_time
        
        # Print summary
        print("\n" + "="*70)
        print("MULTIVIEW WORKFLOW COMPLETE")
        print("="*70)
        print(f"Total time: {timing['total']:.2f}s")
        print(f"\nTiming breakdown:")
        print(f"  - View preprocessing:  {timing['preprocess']:.2f}s")
        print(f"  - Shape generation:    {timing['shape']:.2f}s")
        print(f"  - Texture generation:  {timing['texture']:.2f}s")
        print(f"  - File export:         {timing['export']:.2f}s")
        
        print(f"\nGenerated files:")
        for file_type, path in results.items():
            print(f"  {file_type.upper():10s}: {path}")
        
        print("="*70)
        print()
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='Multiview Hunyuan3D-2 workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Specify views explicitly
  python multiview_workflow.py --front front.jpg --back back.jpg --left left.jpg
  
  # Auto-detect from order (front, back, left, right)
  python multiview_workflow.py front.jpg back.jpg left.jpg right.jpg
  
  # Just front and back
  python multiview_workflow.py --front front.jpg --back back.jpg
  
  # Custom output
  python multiview_workflow.py --front f.jpg --back b.jpg -o outputs/ -n my_model
        """
    )
    
    # Explicit view arguments
    parser.add_argument('--front', type=str,
                       help='Front view image')
    parser.add_argument('--back', type=str,
                       help='Back view image')
    parser.add_argument('--left', type=str,
                       help='Left view image')
    parser.add_argument('--right', type=str,
                       help='Right view image')
    
    # Positional arguments (auto-detected order)
    parser.add_argument('images', nargs='*',
                       help='Images in order: front [back] [left] [right]')
    
    parser.add_argument('--output-dir', '-o', type=str, default='outputs',
                       help='Output directory')
    parser.add_argument('--output-name', '-n', type=str, default='multiview',
                       help='Output file base name')
    parser.add_argument('--turbo', action='store_true',
                       help='Use turbo model (faster, lower quality)')
    parser.add_argument('--no-face', action='store_true',
                       help='Disable face processing')
    parser.add_argument('--no-enhance', action='store_true',
                       help='Disable image enhancement')
    parser.add_argument('--enable-flashvdm', action='store_true',
                       help='Enable Flash VDM (experimental for multiview)')
    parser.add_argument('--device', type=str, default='cuda',
                       help='Device to use')
    
    args = parser.parse_args()
    
    # Build views dictionary
    views = {}
    
    # From explicit arguments
    if args.front:
        views['front'] = args.front
    if args.back:
        views['back'] = args.back
    if args.left:
        views['left'] = args.left
    if args.right:
        views['right'] = args.right
    
    # From positional arguments (auto-detect)
    if args.images:
        view_names = ['front', 'back', 'left', 'right']
        for i, img_path in enumerate(args.images[:4]):
            if i < len(view_names):
                views[view_names[i]] = img_path
    
    # Validate
    if not views:
        parser.error("Please provide at least one view image")
    
    for view_name, view_path in views.items():
        if not os.path.exists(view_path):
            print(f"❌ Error: {view_name} view not found: {view_path}")
            sys.exit(1)
    
    print(f"\nProcessing {len(views)} views:")
    for view_name in ['front', 'back', 'left', 'right']:
        if view_name in views:
            print(f"  {view_name:6s}: {views[view_name]}")
    print()
    
    # Determine subfolder
    subfolder = 'hunyuan3d-dit-v2-mv-turbo' if args.turbo else 'hunyuan3d-dit-v2-mv'
    
    # Initialize workflow
    workflow = Hunyuan3DMultiviewWorkflow(
        model_path='tencent/Hunyuan3D-2mv',
        subfolder=subfolder,
        device=args.device,
        enable_face_processing=not args.no_face,
        enable_image_enhancement=not args.no_enhance,
        enable_flashvdm=args.enable_flashvdm
    )
    
    # Run workflow
    results = workflow.process_views(
        views,
        output_dir=args.output_dir,
        output_name=args.output_name
    )
    
    sys.exit(0)


if __name__ == "__main__":
    main()

