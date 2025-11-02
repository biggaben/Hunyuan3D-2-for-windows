"""
Example: Generate a textured mesh and extract its texture.
This demonstrates the complete workflow.
"""

from PIL import Image
from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline
from hy3dgen.texgen import Hunyuan3DPaintPipeline
import trimesh
import os

# Generate textured mesh
print("=" * 60)
print("Step 1: Generating textured mesh...")
print("=" * 60)

model_path = 'tencent/Hunyuan3D-2'
pipeline_shapegen = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(model_path)
pipeline_texgen = Hunyuan3DPaintPipeline.from_pretrained(model_path)

image_path = 'assets/demo.png'
image = Image.open(image_path).convert("RGBA")
if image.mode == 'RGB':
    rembg = BackgroundRemover()
    image = rembg(image)

print("Generating shape...")
mesh = pipeline_shapegen(image=image)[0]

print("Generating texture...")
mesh = pipeline_texgen(mesh, image=image)

output_glb = 'demo_textured_output.glb'
mesh.export(output_glb)
print(f"✓ Textured mesh saved to: {output_glb}")

# Extract texture
print("\n" + "=" * 60)
print("Step 2: Extracting texture from mesh...")
print("=" * 60)

# Reload mesh
mesh_loaded = trimesh.load(output_glb)

# Extract texture (method from extract_texture.py)
texture_image = None
if hasattr(mesh_loaded, 'visual') and isinstance(mesh_loaded.visual, trimesh.visual.TextureVisuals):
    if hasattr(mesh_loaded.visual, 'material') and mesh_loaded.visual.material is not None:
        if hasattr(mesh_loaded.visual.material, 'image'):
            texture_image = mesh_loaded.visual.material.image

if texture_image:
    texture_output = 'demo_extracted_texture.png'
    texture_image.save(texture_output)
    print(f"✓ Texture extracted to: {texture_output}")
    print(f"  Size: {texture_image.size}")
    print(f"  Mode: {texture_image.mode}")
else:
    print("✗ No texture found")

print("\n" + "=" * 60)
print("Done!")
print("=" * 60)

