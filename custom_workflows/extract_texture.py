#!/usr/bin/env python3
"""
Extract texture from Hunyuan3D-2 generated GLB files.
Based on Hunyuan3D-2's mesh_utils.py implementation.
"""

import trimesh
from PIL import Image
import os
import sys


def extract_texture_from_mesh(mesh_path, output_path=None):
    """
    Extract texture image from a textured mesh file (GLB/OBJ).
    
    Args:
        mesh_path: Path to the textured mesh file
        output_path: Optional output path for texture image
        
    Returns:
        Path to saved texture file, or None if no texture found
    """
    print(f"Loading mesh from: {mesh_path}")
    
    try:
        mesh = trimesh.load(mesh_path)
    except Exception as e:
        print(f"❌ Error loading mesh: {e}")
        return None
    
    # Check if mesh is a Scene (multiple objects)
    if isinstance(mesh, trimesh.Scene):
        print("Detected scene with multiple objects, converting to single mesh...")
        mesh = mesh.dump(concatenate=True)
    
    # Try to extract texture using different methods
    texture_image = None
    
    # Method 1: From TextureVisuals (used by Hunyuan3D-2)
    if hasattr(mesh, 'visual') and isinstance(mesh.visual, trimesh.visual.TextureVisuals):
        if hasattr(mesh.visual, 'material') and mesh.visual.material is not None:
            if hasattr(mesh.visual.material, 'image') and mesh.visual.material.image is not None:
                texture_image = mesh.visual.material.image
                print("✓ Found texture in visual.material.image")
        
        # Method 2: Direct image access
        if texture_image is None and hasattr(mesh.visual, 'image') and mesh.visual.image is not None:
            texture_image = mesh.visual.image
            print("✓ Found texture in visual.image")
    
    if texture_image is None:
        print("❌ No texture found in mesh")
        print(f"   Mesh visual type: {type(mesh.visual)}")
        if hasattr(mesh, 'visual'):
            print(f"   Has material: {hasattr(mesh.visual, 'material')}")
            if hasattr(mesh.visual, 'material') and mesh.visual.material:
                print(f"   Material type: {type(mesh.visual.material)}")
        return None
    
    # Ensure it's a PIL Image
    if not isinstance(texture_image, Image.Image):
        print("Converting texture to PIL Image...")
        if hasattr(texture_image, 'to_pil'):
            texture_image = texture_image.to_pil()
        else:
            print("❌ Cannot convert texture to PIL Image")
            return None
    
    # Determine output path
    if output_path is None:
        base_name = os.path.splitext(mesh_path)[0]
        output_path = f"{base_name}_texture.png"
    
    # Save texture
    try:
        texture_image.save(output_path)
        print(f"✅ Texture saved successfully!")
        print(f"   Output: {output_path}")
        print(f"   Size: {texture_image.size}")
        print(f"   Mode: {texture_image.mode}")
        return output_path
    except Exception as e:
        print(f"❌ Error saving texture: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_texture.py <path_to_mesh_file> [output_path]")
        print("\nExample:")
        print("  python extract_texture.py textured_mesh.glb")
        print("  python extract_texture.py textured_mesh.glb my_texture.png")
        sys.exit(1)
    
    mesh_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(mesh_path):
        print(f"❌ File not found: {mesh_path}")
        sys.exit(1)
    
    result = extract_texture_from_mesh(mesh_path, output_path)
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

