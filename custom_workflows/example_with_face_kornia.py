"""
Example: Using facexlib and kornia to enhance 3D generation workflow.

This demonstrates:
1. Face detection and alignment for portraits
2. Image enhancement with kornia
3. Integration into the 3D generation pipeline
"""

from PIL import Image
import torch

# Standard Hunyuan3D imports
from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
from hy3dgen.texgen import Hunyuan3DPaintPipeline

# New face and enhancement processors
try:
    from hy3dgen.face_processor import FaceProcessor
    FACE_AVAILABLE = True
except ImportError:
    print("facexlib not available. Install with: uv pip install facexlib")
    FACE_AVAILABLE = False

try:
    from hy3dgen.image_enhancer import ImageEnhancer
    KORNIA_AVAILABLE = True
except ImportError:
    print("kornia not available. Install with: uv pip install kornia")
    KORNIA_AVAILABLE = False


def generate_with_enhancements(image_path, is_portrait=True):
    """
    Generate 3D model with face detection and image enhancement.
    
    Args:
        image_path: Path to input image
        is_portrait: Whether image contains a face/portrait
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Load image
    image = Image.open(image_path).convert("RGBA")
    print(f"Original image size: {image.size}")
    
    # Step 1: Face processing (if portrait)
    if is_portrait and FACE_AVAILABLE:
        print("Step 1: Processing face...")
        face_processor = FaceProcessor(device=device)
        
        # Detect and center on face
        image = face_processor.enhance_portrait(image, align=True, center=True)
        print(f"After face processing: {image.size}")
    
    # Step 2: Image enhancement with kornia
    if KORNIA_AVAILABLE:
        print("Step 2: Enhancing image quality...")
        enhancer = ImageEnhancer(device=device)
        image = enhancer.enhance_for_3d(image, sharpen=True, normalize_illum=True)
        print(f"After enhancement: {image.size}")
    
    # Step 3: Background removal
    print("Step 3: Removing background...")
    rembg = BackgroundRemover()
    if image.mode == "RGB":
        image = rembg(image.convert('RGB'))
    
    # Step 4: Generate 3D mesh
    print("Step 4: Generating 3D mesh...")
    model_path = 'tencent/Hunyuan3D-2'
    pipeline_shapegen = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(model_path)
    
    mesh = pipeline_shapegen(image=image)[0]
    print("✓ Mesh generated")
    
    # Step 5: Generate texture
    print("Step 5: Generating texture...")
    pipeline_texgen = Hunyuan3DPaintPipeline.from_pretrained(model_path)
    mesh = pipeline_texgen(mesh, image=image)
    print("✓ Texture generated")
    
    # Save result
    output_path = 'demo_enhanced_3d.glb'
    mesh.export(output_path)
    print(f"✓ Saved to: {output_path}")
    
    return mesh


if __name__ == "__main__":
    # Example usage
    image_path = 'assets/demo.png'  # Change to your image
    
    # For portrait images (faces)
    mesh = generate_with_enhancements(image_path, is_portrait=True)
    
    # For non-portrait images
    # mesh = generate_with_enhancements(image_path, is_portrait=False)
    
    print("\n" + "="*60)
    print("Enhanced 3D generation complete!")
    print("="*60)

