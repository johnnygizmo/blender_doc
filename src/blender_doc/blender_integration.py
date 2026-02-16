"""Blender integration for headless operations."""

import subprocess
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

from .data_structures import BlendFileMetadata


class BlenderIntegration:
    """Handles headless Blender operations."""
    
    def __init__(self, blender_exe: Optional[str] = None):
        """
        Initialize Blender integration.
        
        Args:
            blender_exe: Path to Blender executable. If None, will search in PATH.
        """
        self.blender_exe = blender_exe or self._find_blender()
        if not self.blender_exe:
            raise RuntimeError(
                "Blender executable not found. Please install Blender 5.0+ or "
                "specify the path with --blender-path argument."
            )
    
    @staticmethod
    def _find_blender() -> Optional[str]:
        """Try to find Blender executable in PATH."""
        import shutil
        
        for exe_name in ['blender', 'blender.exe']:
            path = shutil.which(exe_name)
            if path:
                return path
        return None
    
    def extract_blend_dependencies(self, blend_file_path: Path) -> List[str]:
        """
        Extract external file references from a Blend file.
        
        Args:
            blend_file_path: Path to .blend file
        
        Returns:
            List of external file paths referenced in the blend file
        """
        script = """
import bpy
import json
import sys

blend_path = sys.argv[-1]

try:
    bpy.ops.wm.open_mainfile(filepath=blend_path)
except Exception as e:
    print(json.dumps({"error": str(e), "external_files": []}))
    sys.exit(0)

external_files = []

# Check for linked libraries
for library in bpy.data.libraries:
    if library.filepath:
        external_files.append(library.filepath)

# Check for image textures
for image in bpy.data.images:
    if image.filepath and not image.packed_file:
        external_files.append(image.filepath)

# Check for linked objects/collections from other files
for scene in bpy.data.scenes:
    # Check for linked datablocks
    pass

# Remove duplicates and convert to absolute paths
external_files = list(set(external_files))
external_files = [str(Path(f).resolve()) if Path(f).exists() else f 
                   for f in external_files]

print(json.dumps({"external_files": external_files, "error": None}))
"""
        return self._run_blender_script(script, blend_file_path)
    
    def extract_blend_metadata(self, blend_file_path: Path) -> BlendFileMetadata:
        """
        Extract metadata from a Blend file.
        
        Args:
            blend_file_path: Path to .blend file
        
        Returns:
            BlendFileMetadata object with counts and info
        """
        script = """
import bpy
import json
import sys

blend_path = sys.argv[-1]

try:
    bpy.ops.wm.open_mainfile(filepath=blend_path)
except Exception as e:
    print(json.dumps({
        "object_count": 0,
        "scene_count": 0,
        "material_count": 0,
        "mesh_count": 0,
        "total_vertex_count": 0,
        "error": str(e)
    }))
    sys.exit(0)

# Count objects
object_count = len(bpy.data.objects)
scene_count = len(bpy.data.scenes)
material_count = len(bpy.data.materials)

# Count meshes and vertices
mesh_count = len(bpy.data.meshes)
total_vertex_count = 0
for mesh in bpy.data.meshes:
    total_vertex_count += len(mesh.vertices)

print(json.dumps({
    "object_count": object_count,
    "scene_count": scene_count,
    "material_count": material_count,
    "mesh_count": mesh_count,
    "total_vertex_count": total_vertex_count,
    "error": None
}))
"""
        
        try:
            # Create temporary file for script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script)
                script_path = f.name
            
            # Run Blender
            cmd = [
                str(self.blender_exe),
                '--background',
                '--python', script_path,
                '--', str(blend_file_path)
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                
                # Parse output
                output = result.stdout.strip()
                lines = output.split('\n')
                
                # Find JSON line
                for line in lines:
                    if line.startswith('{'):
                        data = json.loads(line)
                        metadata = BlendFileMetadata(
                            object_count=data.get('object_count', 0),
                            scene_count=data.get('scene_count', 0),
                            material_count=data.get('material_count', 0),
                            mesh_count=data.get('mesh_count', 0),
                            total_vertex_count=data.get('total_vertex_count', 0),
                        )
                        return metadata
            
            finally:
                # Clean up temp file
                Path(script_path).unlink(missing_ok=True)
        
        except subprocess.TimeoutExpired:
            print(f"Warning: Blender operation timed out for {blend_file_path}")
        except Exception as e:
            print(f"Warning: Error extracting Blender metadata from {blend_file_path}: {e}")
        
        return BlendFileMetadata()
    
    def _run_blender_script(self, script: str, blend_file_path: Path) -> List[str]:
        """
        Run a Python script in Blender and return parsed JSON output.
        
        Args:
            script: Python code to run in Blender
            blend_file_path: Path to blend file to pass as argument
        
        Returns:
            List of external files
        """
        try:
            # Create temporary file for script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script)
                script_path = f.name
            
            # Run Blender
            cmd = [
                str(self.blender_exe),
                '--background',
                '--python', script_path,
                '--', str(blend_file_path)
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                
                # Parse output
                output = result.stdout.strip()
                lines = output.split('\n')
                
                # Find JSON line
                for line in lines:
                    if line.startswith('{'):
                        data = json.loads(line)
                        if data.get('error'):
                            print(f"Warning: Blender script error: {data['error']}")
                            return []
                        return data.get('external_files', [])
            
            finally:
                # Clean up temp file
                Path(script_path).unlink(missing_ok=True)
        
        except subprocess.TimeoutExpired:
            print(f"Warning: Blender operation timed out for {blend_file_path}")
        except json.JSONDecodeError as e:
            print(f"Warning: Error parsing Blender output: {e}")
        except Exception as e:
            print(f"Warning: Error running Blender script: {e}")
        
        return []
