"""File processing orchestration - processes stack of files."""

from collections import deque
from pathlib import Path
from typing import Optional, List, Set
import sys

from .data_structures import FileEntry, MetadataStore, LinkRegistry, BlendFileMetadata
from .file_scanner import FileScanner
from .metadata_extractor import MetadataExtractor
from .blender_integration import BlenderIntegration


class FileProcessor:
    """Orchestrates the processing of files in the stack."""
    
    def __init__(
        self,
        root_folder: Path,
        metadata_store: MetadataStore,
        link_registry: LinkRegistry,
        blender_integration: Optional[BlenderIntegration] = None,
        follow_external: bool = False,
    ):
        """
        Initialize the file processor.
        
        Args:
            root_folder: Root folder being scanned
            metadata_store: Store for file metadata
            link_registry: Registry for tracking links
            blender_integration: Blender integration instance (optional)
            follow_external: Whether to follow external links outside root folder
        """
        self.root_folder = Path(root_folder)
        self.metadata_store = metadata_store
        self.link_registry = link_registry
        self.blender_integration = blender_integration
        self.follow_external = follow_external
        
        self.scanner = FileScanner(root_folder)
        self.processed_paths: Set[str] = set()  # Avoid processing same file twice
        self.output_list: List[FileEntry] = []
    
    def process_stack(self, processing_stack: deque) -> List[FileEntry]:
        """
        Process the stack of files.
        
        Args:
            processing_stack: Deque of FileEntry objects to process
        
        Returns:
            List of processed FileEntry objects
        """
        while processing_stack:
            entry = processing_stack.popleft()
            
            # Skip if already processed
            if str(entry.path) in self.processed_paths:
                continue
            
            self.processed_paths.add(str(entry.path))
            
            # Check if it's a leaf node
            if self.scanner.is_leaf_node(entry):
                self._process_leaf_node(entry)
            
            # Check if it's a blend file
            elif self.scanner.is_blend_file(entry):
                self._process_blend_file(entry, processing_stack)
            
            # Other file types (unknown)
            else:
                self._process_unknown_file(entry)
            
            entry.processed = True
            self.output_list.append(entry)
        
        return self.output_list
    
    def _process_leaf_node(self, entry: FileEntry) -> None:
        """Process a leaf node file (no external dependencies)."""
        # Extract metadata
        metadata = MetadataExtractor.extract(entry.path, entry.file_type)
        entry.metadata = metadata
        
        print(f"Processed leaf: {entry.name}", file=sys.stderr)
    
    def _process_blend_file(self, entry: FileEntry, processing_stack: deque) -> None:
        """
        Process a Blend file - extract dependencies and metadata.
        
        Args:
            entry: FileEntry for blend file
            processing_stack: Stack to add newly discovered files to
        """
        print(f"Processing Blender file: {entry.name}", file=sys.stderr)
        
        # Extract Blender metadata
        if self.blender_integration:
            blend_metadata = self.blender_integration.extract_blend_metadata(entry.path)
            entry.metadata['blend'] = blend_metadata.to_dict()
            
            # Extract external dependencies
            external_files = self.blender_integration.extract_blend_dependencies(entry.path)
            
            for external_path_str in external_files:
                external_path = Path(external_path_str)
                
                # Check if we should process this file
                if not self.follow_external and not self._is_in_root_folder(external_path):
                    # Just record it but don't process it
                    entry.metadata.setdefault('external_links', []).append(external_path_str)
                    continue
                
                # Check if file exists
                if not external_path.exists():
                    print(
                        f"Warning: External file not found: {external_path_str}",
                        file=sys.stderr
                    )
                    continue
                
                # Create entry for external file if not already processed
                external_entry_path_str = str(external_path)
                if external_entry_path_str not in self.processed_paths:
                    # Check if already in metadata store
                    existing_entry = self.metadata_store.get_entry(external_path)
                    
                    if not existing_entry:
                        # Create new entry for external file
                        external_entry = self._create_entry_for_file(external_path)
                        if external_entry:
                            self.metadata_store.add_entry(external_entry)
                            processing_stack.append(external_entry)
                            
                            # Register link
                            self.link_registry.add_link(str(entry.path), str(external_path))
                            entry.add_link(external_entry)
                    else:
                        # Register link to existing entry
                        self.link_registry.add_link(str(entry.path), external_entry_path_str)
                        entry.add_link(existing_entry)
        else:
            # Blender integration not available - still extract basic metadata
            entry.metadata['blend'] = BlendFileMetadata().to_dict()
        
        print(f"Processed Blender file: {entry.name} ({len(entry.links)} dependencies)",
              file=sys.stderr)
    
    def _process_unknown_file(self, entry: FileEntry) -> None:
        """Process a file of unknown type."""
        # Try to extract any available metadata
        metadata = MetadataExtractor.extract(entry.path, entry.file_type)
        entry.metadata = metadata
        
        print(f"Processed unknown file type: {entry.name}", file=sys.stderr)
    
    def _is_in_root_folder(self, file_path: Path) -> bool:
        """Check if a file path is within the root folder."""
        try:
            file_path.relative_to(self.root_folder)
            return True
        except ValueError:
            return False
    
    def _create_entry_for_file(self, file_path: Path) -> Optional[FileEntry]:
        """Create a FileEntry for a file."""
        try:
            if not file_path.exists() or not file_path.is_file():
                return None
            
            size = file_path.stat().st_size
            folder = file_path.parent
            name = file_path.name
            file_type = self.scanner._get_file_type(name)
            
            entry = FileEntry(
                name=name,
                folder=folder,
                size=size,
                file_type=file_type,
            )
            return entry
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create entry for {file_path}: {e}", file=sys.stderr)
            return None
    
    def get_output_list(self) -> List[FileEntry]:
        """Get the final processed list."""
        return self.output_list
