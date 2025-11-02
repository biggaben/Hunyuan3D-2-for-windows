#!/usr/bin/env python3
"""
Interactive Workflow Launcher
==============================

Simple menu-driven interface for running workflows.

Usage:
    python launcher.py
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header():
    print("\n" + "="*70)
    print("  Hunyuan3D-2 Custom Workflows Launcher")
    print("="*70 + "\n")


def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def select_workflow():
    """Main workflow selection menu"""
    print_header()
    
    print("Select a workflow:\n")
    print("  [1] Complete Workflow - Single image with all enhancements")
    print("  [2] Multiview Workflow - Multiple views (front/back/left/right)")
    print("  [3] Batch Workflow - Process multiple images")
    print("  [4] Exit\n")
    
    choice = get_input("Enter choice (1-4)", "1")
    
    if choice == "1":
        run_complete_workflow()
    elif choice == "2":
        run_multiview_workflow()
    elif choice == "3":
        run_batch_workflow()
    elif choice == "4":
        print("\nGoodbye!\n")
        sys.exit(0)
    else:
        print("\n⚠️  Invalid choice. Please try again.\n")
        select_workflow()


def run_complete_workflow():
    """Interactive complete workflow"""
    print("\n" + "="*70)
    print("  Complete Workflow - Single Image")
    print("="*70 + "\n")
    
    # Get inputs
    image_path = get_input("Input image path")
    
    if not os.path.exists(image_path):
        print(f"\n❌ Error: File not found: {image_path}\n")
        return select_workflow()
    
    output_dir = get_input("Output directory", "outputs")
    
    portrait = get_input("Is this a portrait? (y/n)", "n").lower() == 'y'
    
    model = get_input("Model (h2/mini)", "h2")
    if model not in ['h2', 'mini']:
        model = 'h2'
    
    enhance = get_input("Enable image enhancement? (y/n)", "y").lower() == 'y'
    
    # Build command
    cmd = [
        sys.executable,
        "complete_workflow.py",
        image_path,
        "--output-dir", output_dir,
        "--model", model
    ]
    
    if portrait:
        cmd.append("--portrait")
    
    if not enhance:
        cmd.append("--no-enhance")
    
    print(f"\n{'='*70}")
    print("Running workflow...")
    print(f"{'='*70}\n")
    print(f"Command: {' '.join(cmd)}\n")
    
    # Run
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"\n{'='*70}")
        print("✅ Workflow completed successfully!")
        print(f"{'='*70}\n")
    else:
        print(f"\n{'='*70}")
        print("❌ Workflow failed!")
        print(f"{'='*70}\n")
    
    # Ask to continue
    again = get_input("\nRun another workflow? (y/n)", "y").lower() == 'y'
    if again:
        select_workflow()
    else:
        print("\nGoodbye!\n")


def run_multiview_workflow():
    """Interactive multiview workflow"""
    print("\n" + "="*70)
    print("  Multiview Workflow")
    print("="*70 + "\n")
    
    print("Enter paths for views (leave blank to skip):\n")
    
    views = {}
    for view_name in ['front', 'back', 'left', 'right']:
        path = get_input(f"  {view_name.capitalize()} view")
        if path and os.path.exists(path):
            views[view_name] = path
        elif path:
            print(f"    ⚠️  File not found, skipping: {path}")
    
    if not views:
        print("\n❌ Error: At least one view is required!\n")
        return select_workflow()
    
    output_dir = get_input("\nOutput directory", "outputs")
    output_name = get_input("Output name", "multiview")
    
    turbo = get_input("Use turbo model? (faster, lower quality) (y/n)", "n").lower() == 'y'
    
    # Build command
    cmd = [
        sys.executable,
        "multiview_workflow.py",
        "--output-dir", output_dir,
        "--output-name", output_name
    ]
    
    for view_name, view_path in views.items():
        cmd.extend([f"--{view_name}", view_path])
    
    if turbo:
        cmd.append("--turbo")
    
    print(f"\n{'='*70}")
    print("Running multiview workflow...")
    print(f"{'='*70}\n")
    print(f"Command: {' '.join(cmd)}\n")
    
    # Run
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"\n{'='*70}")
        print("✅ Workflow completed successfully!")
        print(f"{'='*70}\n")
    else:
        print(f"\n{'='*70}")
        print("❌ Workflow failed!")
        print(f"{'='*70}\n")
    
    # Ask to continue
    again = get_input("\nRun another workflow? (y/n)", "y").lower() == 'y'
    if again:
        select_workflow()
    else:
        print("\nGoodbye!\n")


def run_batch_workflow():
    """Interactive batch workflow"""
    print("\n" + "="*70)
    print("  Batch Workflow")
    print("="*70 + "\n")
    
    input_path = get_input("Input folder or pattern (e.g., folder/ or *.jpg)")
    
    output_dir = get_input("Output directory", "batch_outputs")
    
    portrait = get_input("Process as portraits? (y/n)", "n").lower() == 'y'
    
    model = get_input("Model (h2/mini)", "mini")
    if model not in ['h2', 'mini']:
        model = 'mini'
    
    skip_existing = get_input("Skip existing outputs? (y/n)", "y").lower() == 'y'
    
    # Build command
    cmd = [
        sys.executable,
        "batch_workflow.py",
        input_path,
        "--output-dir", output_dir,
        "--model", model
    ]
    
    if portrait:
        cmd.append("--portrait")
    
    if skip_existing:
        cmd.append("--skip-existing")
    
    print(f"\n{'='*70}")
    print("Running batch workflow...")
    print(f"{'='*70}\n")
    print(f"Command: {' '.join(cmd)}\n")
    
    # Run
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"\n{'='*70}")
        print("✅ Workflow completed successfully!")
        print(f"{'='*70}\n")
    else:
        print(f"\n{'='*70}")
        print("❌ Workflow failed!")
        print(f"{'='*70}\n")
    
    # Ask to continue
    again = get_input("\nRun another workflow? (y/n)", "y").lower() == 'y'
    if again:
        select_workflow()
    else:
        print("\nGoodbye!\n")


def main():
    """Main entry point"""
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Check if workflows exist
    workflows = ['complete_workflow.py', 'multiview_workflow.py', 'batch_workflow.py']
    missing = [w for w in workflows if not Path(w).exists()]
    
    if missing:
        print("\n❌ Error: Missing workflow files:")
        for m in missing:
            print(f"  - {m}")
        print("\nPlease ensure all workflow scripts are in the same directory.\n")
        sys.exit(1)
    
    try:
        select_workflow()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

