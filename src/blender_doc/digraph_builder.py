"""Digraph builder for file dependencies grouped by folder hierarchy."""

from pathlib import Path
from typing import Dict, List, Set, Tuple
import networkx as nx

from .data_structures import FileEntry, MetadataStore, LinkRegistry


class DigraphBuilder:
    """Builds a networkx digraph representing file dependencies."""
    
    def __init__(self, metadata_store: MetadataStore, link_registry: LinkRegistry):
        """
        Initialize digraph builder.
        
        Args:
            metadata_store: Store containing all file metadata
            link_registry: Registry containing all links between files
        """
        self.metadata_store = metadata_store
        self.link_registry = link_registry
        self.digraph: nx.DiGraph = nx.DiGraph()
    
    def build_by_folder_hierarchy(self, root_folder: Path) -> nx.DiGraph:
        """
        Build a digraph with files as nodes, grouped by folder.
        
        Nodes represent files, edges represent dependencies.
        Files are visually grouped by their folder location.
        
        Args:
            root_folder: Root folder for the project
        
        Returns:
            networkx DiGraph
        """
        self.digraph = nx.DiGraph()
        root_folder = Path(root_folder)
        
        # Create node for each file
        for entry in self.metadata_store.get_all_entries():
            node_id = self._get_file_node_id(entry, root_folder)
            folder_group = self._get_folder_group(entry, root_folder)
            
            self.digraph.add_node(
                node_id,
                file_name=entry.name,
                file_path=str(entry.path),
                folder=str(entry.folder),
                folder_group=folder_group,
                size=entry.size,
                file_type=entry.file_type,
                label=entry.name,
            )
        
        # Create edges based on links between files
        for entry in self.metadata_store.get_all_entries():
            source_node_id = self._get_file_node_id(entry, root_folder)
            
            # Check links from this file
            for linked_entry in entry.links:
                target_node_id = self._get_file_node_id(linked_entry, root_folder)
                
                # Add edge
                if not self.digraph.has_edge(source_node_id, target_node_id):
                    self.digraph.add_edge(
                        source_node_id,
                        target_node_id,
                        weight=1,
                    )
                else:
                    # Increment weight if edge already exists
                    self.digraph[source_node_id][target_node_id]['weight'] += 1
        
        return self.digraph
    
    def _get_file_node_id(self, entry: FileEntry, root_folder: Path) -> str:
        """Get a unique node ID for a file."""
        try:
            rel_path = entry.path.relative_to(root_folder)
            return str(rel_path).replace('\\', '/')
        except ValueError:
            return str(entry.path)
    
    def _get_folder_group(self, entry: FileEntry, root_folder: Path) -> str:
        """Get the folder group for visualization purposes."""
        try:
            rel_path = entry.folder.relative_to(root_folder)
            folder_str = str(rel_path).replace('\\', '/')
            return folder_str if folder_str != '.' else 'root'
        except ValueError:
            return entry.folder.name
    
    def get_digraph(self) -> nx.DiGraph:
        """Get the built digraph."""
        return self.digraph
    
    def get_statistics(self) -> Dict:
        """Get statistics about the digraph."""
        return {
            'file_count': self.digraph.number_of_nodes(),
            'link_count': self.digraph.number_of_edges(),
            'density': nx.density(self.digraph) if self.digraph.number_of_nodes() > 0 else 0,
            'is_dag': nx.is_directed_acyclic_graph(self.digraph),
            'connected_components': nx.number_weakly_connected_components(self.digraph) if self.digraph.number_of_nodes() > 0 else 0,
        }
    
    def get_folder_groups(self) -> Dict[str, List[str]]:
        """Get files grouped by folder."""
        groups: Dict[str, List[str]] = {}
        
        for node in self.digraph.nodes():
            folder_group = self.digraph.nodes[node].get('folder_group', 'root')
            if folder_group not in groups:
                groups[folder_group] = []
            groups[folder_group].append(node)
        
        return groups

