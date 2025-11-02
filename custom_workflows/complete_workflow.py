#!/usr/bin/env python3
"""
Complete Hunyuan3D-2 Workflow with All Custom Tools
====================================================

This workflow integrates all custom tools into a single pipeline:
1. Face detection and alignment (for portraits)
2. Image enhancement (kornia)
3. Background removal
4. 3D mesh generation
5. Texture generation
6. Export as OBJ + PNG + GLB
7. Texture extraction

Usage:
    python complete_workflow.py input.jpg --portrait --output-dir outputs/
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
    print("⚠️  facexlib not available. Face processing disabled.")
    FACE_AVAILABLE = False

try:
    from hy3dgen.image_enhancer import ImageEnhancer
    KORNIA_AVAILABLE = True
except ImportError:
    print("⚠️  kornia not available. Image enhancement disabled.")
    KORNIA_AVAILABLE = False

from extract_texture import extract_texture_from_mesh


class Hunyuan3DCompleteWorkflow:
    """Complete 3D generation workflow with all enhancements"""
    
    def __init__(self, 
                 model_path='tencent/Hunyuan3D-2',  # Full H2 model for best quality
                 device='cuda',
                 enable_face_processing=True,  # Always enabled for best results
                 enable_image_enhancement=True,  # Always enabled for best quality
                 enable_flashvdm=True,  # Faster without quality loss
                 octree_resolution=384,  # High resolution for detail
                 num_inference_steps=50,  # Maximum quality steps
                 guidance_scale=7.5):  # Better adherence
        """
        Initialize the complete workflow.
        
        Args:
            model_path: Model to use ('tencent/Hunyuan3D-2' or 'tencent/Hunyuan3D-2mini')
            device: 'cuda' or 'cpu'
            enable_face_processing: Enable face detection and alignment
            enable_image_enhancement: Enable kornia image enhancement
            enable_flashvdm: Enable flash VDM for faster generation
        """
        self.device = device
        self.enable_face = enable_face_processing and FACE_AVAILABLE
        self.enable_enhance = enable_image_enhancement and KORNIA_AVAILABLE
        self.octree_resolution = octree_resolution
        self.num_inference_steps = num_inference_steps
        self.guidance_scale = guidance_scale
        
        print("="*70)
        print("Initializing Hunyuan3D-2 Complete Workflow - BEST QUALITY MODE")
        print("="*70)
        print(f"Model: {model_path.split('/')[-1]} (Full 2.6B)")
        print(f"Octree Resolution: {octree_resolution} (High Detail)")
        print(f"Inference Steps: {num_inference_steps} (Maximum Quality)")
        print(f"Guidance Scale: {guidance_scale}")
        print("="*70)
        
        # Initialize custom tools
        if self.enable_face:
            print("✓ Initializing face processor...")
            self.face_processor = FaceProcessor(device=device)
        
        if self.enable_enhance:
            print("✓ Initializing image enhancer...")
            self.enhancer = ImageEnhancer(device=device)
        
        # Initialize standard tools
        print("✓ Initializing background remover...")
        self.rembg = BackgroundRemover()
        
        print("✓ Loading shape generation model...")
        self.pipeline_shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(model_path)
        
        if enable_flashvdm:
            print("✓ Enabling Flash VDM...")
            self.pipeline_shape.enable_flashvdm()
        
        print("✓ Loading texture generation model...")
        self.pipeline_tex = Hunyuan3DPaintPipeline.from_pretrained('tencent/Hunyuan3D-2')
        
        print("="*70)
        print("Initialization complete!")
        print("="*70)
        print()
    
    def process_single_image(self, image_path, output_dir='outputs', is_portrait=False):
        """
        Process a single image through the complete pipeline.
        
        Args:
            image_path: Path to input image
            output_dir: Output directory for results
            is_portrait: Whether image contains a face/portrait
            
        Returns:
            dict: Paths to generated files
        """
        start_time = time.time()
        image_name = Path(image_path).stem
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timing = {}
        
        print("\n" + "="*70)
        print(f"Processing: {image_path}")
        print("="*70)
        
        # Stage 1: Load and preprocess image
        print("\n[1/7] Loading image...")
        t0 = time.time()
        image = Image.open(image_path).convert("RGBA")
        print(f"      Original size: {image.size}")
        timing['load'] = time.time() - t0
        
        # Stage 2: Face processing (if portrait)
        if is_portrait and self.enable_face:
            print("\n[2/7] Processing face...")
            t0 = time.time()
            faces = self.face_processor.detect_faces(image)
            
            if len(faces) > 0:
                print(f"      ✓ Detected {len(faces)} face(s)")
                image = self.face_processor.enhance_portrait(
                    image, align=True, center=True
                )
                print(f"      ✓ Face centered and aligned")
            else:
                print(f"      ⚠️  No faces detected, skipping face processing")
            
            timing['face'] = time.time() - t0
        else:
            print("\n[2/7] Face processing: Skipped")
        
        # Stage 3: Image enhancement
        if self.enable_enhance:
            print("\n[3/7] Enhancing image (HIGH QUALITY)...")
            t0 = time.time()
            # Use higher sharpness factor for best quality
            image = self.enhancer.enhance_sharpness(image, factor=1.5)
            image = self.enhancer.normalize_illumination(image)
            print(f"      ✓ Applied maximum sharpening (1.5x)")
            print(f"      ✓ Normalized illumination")
            timing['enhance'] = time.time() - t0
        else:
            print("\n[3/7] Image enhancement: Skipped")
        
        # Stage 4: Background removal
        print("\n[4/7] Removing background...")
        t0 = time.time()
        if image.mode == "RGB":
            image = self.rembg(image.convert('RGB'))
        timing['rembg'] = time.time() - t0
        print(f"      ✓ Background removed ({timing['rembg']:.2f}s)")
        
        # Stage 5: Generate 3D mesh (HIGH QUALITY)
        print("\n[5/7] Generating 3D mesh (HIGH QUALITY SETTINGS)...")
        t0 = time.time()
        mesh = self.pipeline_shape(
            image=image,
            num_inference_steps=self.num_inference_steps,
            guidance_scale=self.guidance_scale,
            octree_resolution=self.octree_resolution,
            num_chunks=20000,
            generator=torch.manual_seed(12345)
        )[0]
        timing['shape'] = time.time() - t0
        print(f"      ✓ High-quality mesh generated ({timing['shape']:.2f}s)")
        print(f"      Faces: {len(mesh.faces):,}, Vertices: {len(mesh.vertices):,}")
        print(f"      Quality: Octree {self.octree_resolution}, Steps {self.num_inference_steps}")
        
        # Stage 6: Generate texture
        print("\n[6/7] Generating texture...")
        t0 = time.time()
        textured_mesh = self.pipeline_tex(mesh, image=image)
        timing['texture'] = time.time() - t0
        print(f"      ✓ Texture generated ({timing['texture']:.2f}s)")
        
        # Stage 7: Export files
        print("\n[7/7] Exporting files...")
        t0 = time.time()
        
        results = {}
        
        # Export GLB
        glb_path = output_dir / f"{image_name}_textured.glb"
        textured_mesh.export(str(glb_path))
        results['glb'] = str(glb_path)
        print(f"      ✓ Exported GLB: {glb_path.name}")
        
        # Export OBJ (automatically creates separate texture PNG)
        obj_path = output_dir / f"{image_name}_textured.obj"
        textured_mesh.export(str(obj_path))
        results['obj'] = str(obj_path)
        print(f"      ✓ Exported OBJ: {obj_path.name}")
        
        # Extract texture separately
        texture_path = extract_texture_from_mesh(str(glb_path), 
                                                 str(output_dir / f"{image_name}_texture.png"))
        if texture_path:
            results['texture'] = texture_path
            print(f"      ✓ Extracted texture: {Path(texture_path).name}")
        
        timing['export'] = time.time() - t0
        timing['total'] = time.time() - start_time
        
        # Print summary
        print("\n" + "="*70)
        print("WORKFLOW COMPLETE")
        print("="*70)
        print(f"Total time: {timing['total']:.2f}s")
        print(f"\nTiming breakdown:")
        print(f"  - Image loading:      {timing.get('load', 0):.2f}s")
        if 'face' in timing:
            print(f"  - Face processing:    {timing['face']:.2f}s")
        if 'enhance' in timing:
            print(f"  - Image enhancement:  {timing['enhance']:.2f}s")
        print(f"  - Background removal: {timing['rembg']:.2f}s")
        print(f"  - Shape generation:   {timing['shape']:.2f}s")
        print(f"  - Texture generation: {timing['texture']:.2f}s")
        print(f"  - File export:        {timing['export']:.2f}s")
        
        print(f"\nGenerated files:")
        for file_type, path in results.items():
            print(f"  {file_type.upper():10s}: {path}")
        
        print("="*70)
        print()
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='Complete Hunyuan3D-2 workflow with all custom tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python complete_workflow.py input.jpg
  
  # Portrait with all enhancements
  python complete_workflow.py portrait.jpg --portrait
  
  # Custom output directory
  python complete_workflow.py input.jpg --output-dir my_outputs/
  
  # Use mini model (faster, lower quality)
  python complete_workflow.py input.jpg --model mini
  
  # Disable specific features
  python complete_workflow.py input.jpg --no-face --no-enhance
        """
    )
    
    parser.add_argument('input', type=str,
                       help='Input image path')
    parser.add_argument('--output-dir', '-o', type=str, default='outputs',
                       help='Output directory (default: outputs/)')
    parser.add_argument('--portrait', action='store_true',
                       help='Enable face processing for portraits')
    parser.add_argument('--model', type=str, default='h2',
                       choices=['h2', 'mini'],
                       help='Model to use: h2 (full, default) or mini (faster)')
    parser.add_argument('--no-face', action='store_true',
                       help='Disable face processing')
    parser.add_argument('--no-enhance', action='store_true',
                       help='Disable image enhancement')
    parser.add_argument('--no-flashvdm', action='store_true',
                       help='Disable Flash VDM (slower but may be more stable)')
    parser.add_argument('--device', type=str, default='cuda',
                       choices=['cuda', 'cpu'],
                       help='Device to use (default: cuda)')
    
    args = parser.parse_args()
    
    # Validate input
    if not os.path.exists(args.input):
        print(f"❌ Error: Input file not found: {args.input}")
        sys.exit(1)
    
    # Determine model path
    model_path = 'tencent/Hunyuan3D-2' if args.model == 'h2' else 'tencent/Hunyuan3D-2mini'
    
    # Initialize workflow
    workflow = Hunyuan3DCompleteWorkflow(
        model_path=model_path,
        device=args.device,
        enable_face_processing=not args.no_face,
        enable_image_enhancement=not args.no_enhance,
        enable_flashvdm=not args.no_flashvdm
    )
    
    # Run workflow
    results = workflow.process_single_image(
        args.input,
        output_dir=args.output_dir,
        is_portrait=args.portrait
    )
    
    sys.exit(0)


if __name__ == "__main__":
    main()

