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
from pathlib import Path

blend_path = sys.argv[-1]
blend_dir = str(Path(blend_path).parent)

try:
    bpy.ops.wm.open_mainfile(filepath=blend_path)
except Exception as e:
    print(json.dumps({"error": str(e), "external_files": []}))
    sys.exit(0)

external_files = set()

def resolve_path(path_str, base_dir):
    \"\"\"Resolve a path, handling Blender relative paths.\"\"\"
    if not path_str:
        return None
    # Blender uses // for relative paths
    if path_str.startswith('//'):
        path_str = str(Path(base_dir) / path_str[2:])
    # Make absolute if relative
    if not Path(path_str).is_absolute():
        path_str = str(Path(base_dir) / path_str)
    try:
        # Normalize the path
        resolved = str(Path(path_str).resolve())
        return resolved
    except:
        return None

# 1. Check for linked libraries (primary source)
for library in bpy.data.libraries:
    if library.filepath:
        lib_path = resolve_path(library.filepath, blend_dir)
        if lib_path:
            external_files.add(lib_path)

# 2. Check for linked objects directly
for obj in bpy.data.objects:
    # Objects can be linked from another file
    if obj.library:
        lib_path = resolve_path(obj.library.filepath, blend_dir)
        if lib_path:
            external_files.add(lib_path)
    
    # Check object data (mesh, curve, etc)
    if hasattr(obj, 'data') and obj.data:
        if hasattr(obj.data, 'library') and obj.data.library:
            lib_path = resolve_path(obj.data.library.filepath, blend_dir)
            if lib_path:
                external_files.add(lib_path)

# 3. Check for linked collections
for collection in bpy.data.collections:
    if collection.library:
        lib_path = resolve_path(collection.library.filepath, blend_dir)
        if lib_path:
            external_files.add(lib_path)

# 4. Check for linked materials
for material in bpy.data.materials:
    if material.library:
        lib_path = resolve_path(material.library.filepath, blend_dir)
        if lib_path:
            external_files.add(lib_path)

# 5. Check for image textures
for image in bpy.data.images:
    if image.filepath and not image.packed_file:
        img_path = resolve_path(image.filepath, blend_dir)
        if img_path and Path(img_path).exists():
            external_files.add(img_path)

# 6. Check for linked actions (animations)
for action in bpy.data.actions:
    if action.library:
        lib_path = resolve_path(action.library.filepath, blend_dir)
        if lib_path:
            external_files.add(lib_path)

# 7. Check for linked node trees (shader, compositor, geometry)
for node_tree in bpy.data.node_groups:
    if node_tree.library:
        lib_path = resolve_path(node_tree.library.filepath, blend_dir)
        if lib_path:
            external_files.add(lib_path)

# 8. Check particle systems for external dependencies
for obj in bpy.data.objects:
    if hasattr(obj, 'particle_systems'):
        for ps in obj.particle_systems:
            if hasattr(ps, 'settings') and hasattr(ps.settings, 'instance_collection'):
                if ps.settings.instance_collection:
                    coll = ps.settings.instance_collection
                    if hasattr(coll, 'library') and coll.library:
                        lib_path = resolve_path(coll.library.filepath, blend_dir)
                        if lib_path:
                            external_files.add(lib_path)

# 9. Check for linked meshes, curves, etc
for mesh in bpy.data.meshes:
    if hasattr(mesh, 'library') and mesh.library:
        lib_path = resolve_path(mesh.library.filepath, blend_dir)
        if lib_path:
            external_files.add(lib_path)

for curve in bpy.data.curves:
    if hasattr(curve, 'library') and curve.library:
        lib_path = resolve_path(curve.library.filepath, blend_dir)
        if lib_path:
            external_files.add(lib_path)

# Convert to sorted list
external_files = sorted(list(external_files))

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
