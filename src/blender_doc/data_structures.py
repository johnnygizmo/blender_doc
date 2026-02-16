"""Data structures for Blender project documentation."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import os


@dataclass
class FileEntry:
    """Represents a file in the Blender project with metadata and links."""
    
    name: str
    folder: Path
    size: int  # in bytes
    file_type: str  # extension or mimetype
    path: Path = field(init=False)
    
    # File metadata (content-specific information)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Links to other files (dependencies)
    links: List['FileEntry'] = field(default_factory=list)
    
    # Whether this file has been processed
    processed: bool = False
    
    def __post_init__(self):
        """Set full path after initialization."""
        self.path = self.folder / self.name
    
    def add_link(self, target_file: 'FileEntry') -> None:
        """Add a dependency link to another file."""
        if target_file not in self.links:
            self.links.append(target_file)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'name': self.name,
            'folder': str(self.folder),
            'path': str(self.path),
            'size': self.size,
            'file_type': self.file_type,
            'metadata': self.metadata,
            'link_count': len(self.links),
            'linked_files': [link.name for link in self.links],
            'processed': self.processed,
        }


@dataclass
class BlendFileMetadata:
    """Metadata specific to Blender files."""
    
    object_count: int = 0
    scene_count: int = 0
    material_count: int = 0
    mesh_count: int = 0
    total_vertex_count: int = 0
    external_links: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'object_count': self.object_count,
            'scene_count': self.scene_count,
            'material_count': self.material_count,
            'mesh_count': self.mesh_count,
            'total_vertex_count': self.total_vertex_count,
            'external_links_count': len(self.external_links),
        }


class MetadataStore:
    """Manages and indexes all FileEntry metadata."""
    
    def __init__(self):
        self._entries: Dict[str, FileEntry] = {}  # path -> FileEntry
        self._by_type: Dict[str, List[FileEntry]] = {}  # type -> entries
        self._by_folder: Dict[str, List[FileEntry]] = {}  # folder -> entries
        self._root_folder: Optional[Path] = None
    
    def add_entry(self, entry: FileEntry) -> None:
        """Add a file entry to the store."""
        entry_key = str(entry.path)
        self._entries[entry_key] = entry
        
        # Index by type
        if entry.file_type not in self._by_type:
            self._by_type[entry.file_type] = []
        self._by_type[entry.file_type].append(entry)
        
        # Index by folder
        folder_key = str(entry.folder)
        if folder_key not in self._by_folder:
            self._by_folder[folder_key] = []
        self._by_folder[folder_key].append(entry)
    
    def get_entry(self, path: Path) -> Optional[FileEntry]:
        """Retrieve an entry by path."""
        return self._entries.get(str(path))
    
    def get_by_type(self, file_type: str) -> List[FileEntry]:
        """Get all entries of a specific type."""
        return self._by_type.get(file_type, [])
    
    def get_by_folder(self, folder: Path) -> List[FileEntry]:
        """Get all entries in a specific folder."""
        return self._by_folder.get(str(folder), [])
    
    def get_all_entries(self) -> List[FileEntry]:
        """Get all entries."""
        return list(self._entries.values())
    
    def set_root_folder(self, folder: Path) -> None:
        """Set the root folder for relative path calculations."""
        self._root_folder = folder
    
    def get_root_folder(self) -> Optional[Path]:
        """Get the root folder."""
        return self._root_folder
    
    def get_relative_path(self, entry: FileEntry) -> str:
        """Get relative path from root folder."""
        if not self._root_folder:
            return str(entry.path)
        try:
            return str(entry.path.relative_to(self._root_folder))
        except ValueError:
            return str(entry.path)
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics about the metadata store."""
        return {
            'total_entries': len(self._entries),
            'unique_types': len(self._by_type),
            'total_folders': len(self._by_folder),
            'total_size': sum(e.size for e in self._entries.values()),
            'processed_entries': sum(1 for e in self._entries.values() if e.processed),
        }


class LinkRegistry:
    """Manages file interdependencies and prevents cyclic link issues."""
    
    def __init__(self):
        self._links: Dict[str, set] = {}  # source -> set of target paths
        self._reverse_links: Dict[str, set] = {}  # target -> set of source paths
        self._visited: set = set()  # for cycle detection
    
    def add_link(self, source_path: str, target_path: str) -> bool:
        """
        Add a link between two files.
        Returns False if this would create a cycle, True otherwise.
        """
        if self._would_create_cycle(source_path, target_path):
            return False
        
        if source_path not in self._links:
            self._links[source_path] = set()
        self._links[source_path].add(target_path)
        
        if target_path not in self._reverse_links:
            self._reverse_links[target_path] = set()
        self._reverse_links[target_path].add(source_path)
        
        return True
    
    def _would_create_cycle(self, source: str, target: str) -> bool:
        """Check if adding a link would create a cycle."""
        self._visited.clear()
        return self._has_path_to(target, source)
    
    def _has_path_to(self, start: str, goal: str) -> bool:
        """DFS to check if there's a path from start to goal."""
        if start == goal:
            return True
        if start in self._visited:
            return False
        self._visited.add(start)
        
        for next_node in self._links.get(start, set()):
            if self._has_path_to(next_node, goal):
                return True
        
        return False
    
    def get_links(self, source_path: str) -> set:
        """Get all outgoing links from a source file."""
        return self._links.get(source_path, set())
    
    def get_reverse_links(self, target_path: str) -> set:
        """Get all incoming links to a target file."""
        return self._reverse_links.get(target_path, set())
    
    def get_all_links(self) -> Dict[str, set]:
        """Get all links."""
        return self._links.copy()
    
    def get_all_reverse_links(self) -> Dict[str, set]:
        """Get all reverse links."""
        return self._reverse_links.copy()
