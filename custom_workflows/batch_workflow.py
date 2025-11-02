#!/usr/bin/env python3
"""
Batch Processing Workflow
==========================

Process multiple images in batch using the complete workflow.

Usage:
    python batch_workflow.py input_folder/ --output-dir batch_outputs/
    python batch_workflow.py *.jpg --portrait
"""

import argparse
import os
import sys
from pathlib import Path
from glob import glob

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from complete_workflow import Hunyuan3DCompleteWorkflow


def find_images(pattern_or_dir):
    """Find all images matching pattern or in directory"""
    path = Path(pattern_or_dir)
    
    if path.is_dir():
        # Find all images in directory
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.bmp']
        images = []
        for ext in extensions:
            images.extend(path.glob(ext))
            images.extend(path.glob(ext.upper()))
        return sorted(images)
    elif '*' in str(pattern_or_dir):
        # Glob pattern
        return sorted(glob(pattern_or_dir))
    elif path.exists():
        # Single file
        return [path]
    else:
        return []


def main():
    parser = argparse.ArgumentParser(
        description='Batch process multiple images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all images in a folder
  python batch_workflow.py input_folder/
  
  # Process specific pattern
  python batch_workflow.py images/*.jpg --portrait
  
  # Process with custom settings
  python batch_workflow.py *.png --output-dir results/ --model mini
        """
    )
    
    parser.add_argument('input', type=str,
                       help='Input directory, glob pattern, or file')
    parser.add_argument('--output-dir', '-o', type=str, default='batch_outputs',
                       help='Output directory')
    parser.add_argument('--portrait', action='store_true',
                       help='Enable face processing (apply to all)')
    parser.add_argument('--model', type=str, default='h2',
                       choices=['h2', 'mini'])
    parser.add_argument('--no-face', action='store_true')
    parser.add_argument('--no-enhance', action='store_true')
    parser.add_argument('--no-flashvdm', action='store_true')
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip if output already exists')
    
    args = parser.parse_args()
    
    # Find images
    images = find_images(args.input)
    
    if not images:
        print(f"❌ No images found matching: {args.input}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"Batch Processing: {len(images)} images")
    print(f"{'='*70}\n")
    
    for i, img_path in enumerate(images, 1):
        print(f"Image {i}/{len(images)}: {img_path.name}")
    
    print(f"\n{'='*70}\n")
    
    # Initialize workflow once
    model_path = 'tencent/Hunyuan3D-2' if args.model == 'h2' else 'tencent/Hunyuan3D-2mini'
    
    workflow = Hunyuan3DCompleteWorkflow(
        model_path=model_path,
        device=args.device,
        enable_face_processing=not args.no_face,
        enable_image_enhancement=not args.no_enhance,
        enable_flashvdm=not args.no_flashvdm
    )
    
    # Process each image
    success = 0
    failed = []
    
    for i, img_path in enumerate(images, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(images)}] Processing: {img_path.name}")
        print(f"{'='*70}")
        
        try:
            # Check if already processed
            output_glb = Path(args.output_dir) / f"{img_path.stem}_textured.glb"
            if args.skip_existing and output_glb.exists():
                print(f"⏭️  Skipping (already exists): {output_glb.name}")
                continue
            
            # Process
            results = workflow.process_single_image(
                str(img_path),
                output_dir=args.output_dir,
                is_portrait=args.portrait
            )
            
            success += 1
            
        except Exception as e:
            print(f"\n❌ Error processing {img_path.name}: {e}")
            failed.append(str(img_path))
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*70}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"Total: {len(images)} images")
    print(f"✓ Success: {success}")
    if failed:
        print(f"✗ Failed: {len(failed)}")
        for f in failed:
            print(f"  - {f}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

