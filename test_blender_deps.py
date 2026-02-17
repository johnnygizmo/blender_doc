#!/usr/bin/env python
"""Test script to diagnose Blender dependency extraction."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from blender_doc.blender_integration import BlenderIntegration

def test_dependencies():
    """Test extracting dependencies from blend files."""
    project_folder = Path(r"C:\Users\johnn\Dropbox\ProjectFiles\Assets\Characters")
    
    # Find blend files
    blend_files = list(project_folder.glob("*.blend"))
    
    print(f"Found {len(blend_files)} blend files\n")
    
    # Try to initialize Blender integration
    try:
        blender = BlenderIntegration()
        print("✓ Blender integration initialized\n")
    except RuntimeError as e:
        print(f"✗ Blender integration failed: {e}\n")
        return
    
    # Test each blend file
    for blend_file in blend_files:
        print(f"Processing: {blend_file.name}")
        
        # Extract dependencies
        deps = blender.extract_blend_dependencies(blend_file)
        
        if deps:
            print(f"  Found {len(deps)} dependencies:")
            for dep in deps:
                print(f"    - {Path(dep).name}")
        else:
            print(f"  No dependencies found")
        
        print()

if __name__ == '__main__':
    test_dependencies()
