"""File scanning module for Blender project documentation."""

import os
import mimetypes
from pathlib import Path
from typing import List, Tuple, Set
from collections import deque

from .data_structures import FileEntry


class FileScanner:
    """Scans directories and builds initial FileEntry objects."""
    
    # File types that are leaf nodes (don't have external links we need to track)
    LEAF_TYPES = {
        'jpg', 'jpeg', 'png', 'tiff', 'tif', 'exr', 'hdr', 'bmp', 'gif', 'webp',
        'mp3', 'wav', 'flac', 'aac', 'ogg', 'aiff',
        'txt', 'md', 'rst', 'csv', 'json', 'xml', 'yaml', 'yml',
        'ttf', 'otf', 'woff', 'woff2',
        'pdf', 'obj', 'fbx', 'usd', 'usda', 'glb', 'gltf',
    }
    
    # Files to skip during scanning
    SKIP_PATTERNS = {
        '.git', '.gitignore', '__pycache__', '.DS_Store', 'thumbs.db',
        '.pytest_cache', '.venv', 'venv', 'node_modules',
    }
    
    def __init__(self, root_folder: Path):
        """Initialize scanner for a root folder."""
        self.root_folder = Path(root_folder)
        if not self.root_folder.exists():
            raise FileNotFoundError(f"Folder does not exist: {self.root_folder}")
        if not self.root_folder.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {self.root_folder}")
    
    def scan(self, recursive: bool = True) -> Tuple[List[FileEntry], deque]:
        """
        Scan the folder and return FileEntry objects and a processing stack.
        
        Returns:
            Tuple of (file_entries, processing_stack)
            processing_stack is a deque for BFS processing
        """
        entries = []
        processing_stack = deque()
        
        if recursive:
            for root, dirs, files in os.walk(self.root_folder):
                # Filter out directories to skip
                dirs[:] = [d for d in dirs if d not in self.SKIP_PATTERNS]
                
                folder_path = Path(root)
                for filename in files:
                    if self._should_skip(filename):
                        continue
                    
                    entry = self._create_file_entry(folder_path, filename)
                    if entry:
                        entries.append(entry)
                        processing_stack.append(entry)
        else:
            # Non-recursive: only scan root folder
            for filename in os.listdir(self.root_folder):
                if self._should_skip(filename):
                    continue
                
                file_path = self.root_folder / filename
                if file_path.is_file():
                    entry = self._create_file_entry(self.root_folder, filename)
                    if entry:
                        entries.append(entry)
                        processing_stack.append(entry)
        
        return entries, processing_stack
    
    def _should_skip(self, filename: str) -> bool:
        """Check if a file should be skipped."""
        if filename in self.SKIP_PATTERNS:
            return True
        if filename.startswith('.'):
            return True
        return False
    
    def _create_file_entry(self, folder: Path, filename: str) -> FileEntry | None:
        """Create a FileEntry from a file."""
        file_path = folder / filename
        
        try:
            if not file_path.exists() or not file_path.is_file():
                return None
            
            size = file_path.stat().st_size
            file_type = self._get_file_type(filename)
            
            entry = FileEntry(
                name=filename,
                folder=folder,
                size=size,
                file_type=file_type,
            )
            return entry
        
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not access file {file_path}: {e}")
            return None
    
    def _get_file_type(self, filename: str) -> str:
        """Get file type from extension or mimetype."""
        # Try to get extension first
        _, ext = os.path.splitext(filename)
        if ext:
            ext = ext.lstrip('.').lower()
            return ext
        
        # Fall back to mimetype
        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype:
            return mimetype.split('/')[-1]
        
        return 'unknown'
    
    def is_leaf_node(self, entry: FileEntry) -> bool:
        """Check if a file is a leaf node (no external links)."""
        # Blend files are not leaf nodes - they may have dependencies
        if entry.file_type == 'blend':
            return False
        
        # Check against known leaf types
        return entry.file_type in self.LEAF_TYPES
    
    def is_blend_file(self, entry: FileEntry) -> bool:
        """Check if a file is a Blender file."""
        return entry.file_type == 'blend'
