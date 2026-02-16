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
        Build a digraph grouped by folder hierarchy.
        
        Nodes represent folders, edges represent dependencies between files in those folders.
        
        Args:
            root_folder: Root folder for the project
        
        Returns:
            networkx DiGraph
        """
        self.digraph = nx.DiGraph()
        root_folder = Path(root_folder)
        
        # First pass: create folder nodes
        folders_with_files: Dict[str, List[FileEntry]] = {}
        
        for entry in self.metadata_store.get_all_entries():
            folder_str = str(entry.folder)
            if folder_str not in folders_with_files:
                folders_with_files[folder_str] = []
            folders_with_files[folder_str].append(entry)
        
        # Create nodes for each folder
        for folder_path, files in folders_with_files.items():
            # Calculate relative path from root
            try:
                folder = Path(folder_path)
                rel_path = folder.relative_to(root_folder)
            except ValueError:
                rel_path = Path(folder_path).name
            
            node_id = str(rel_path) if str(rel_path) != '.' else 'root'
            
            self.digraph.add_node(
                node_id,
                folder_path=folder_path,
                file_count=len(files),
                total_size=sum(f.size for f in files),
                files=files,
            )
        
        # Second pass: create edges based on links between files
        processed_edges: Set[Tuple[str, str]] = set()
        
        for entry in self.metadata_store.get_all_entries():
            source_folder = self._get_node_id(entry.folder, root_folder)
            
            # Check links from this file
            for linked_entry in entry.links:
                target_folder = self._get_node_id(linked_entry.folder, root_folder)
                
                # Only add edge if folders are different (avoid self-loops)
                if source_folder != target_folder:
                    edge_key = (source_folder, target_folder)
                    if edge_key not in processed_edges:
                        # Check for existing edge and increment weight
                        if self.digraph.has_edge(source_folder, target_folder):
                            self.digraph[source_folder][target_folder]['weight'] += 1
                            self.digraph[source_folder][target_folder]['file_links'].append(
                                (entry.name, linked_entry.name)
                            )
                        else:
                            self.digraph.add_edge(
                                source_folder,
                                target_folder,
                                weight=1,
                                file_links=[(entry.name, linked_entry.name)],
                            )
                        processed_edges.add(edge_key)
        
        return self.digraph
    
    def _get_node_id(self, folder: Path, root_folder: Path) -> str:
        """Get the node ID for a folder."""
        try:
            rel_path = folder.relative_to(root_folder)
            node_id = str(rel_path).replace('\\', '/')
            return node_id if node_id != '.' else 'root'
        except ValueError:
            return folder.name
    
    def get_digraph(self) -> nx.DiGraph:
        """Get the built digraph."""
        return self.digraph
    
    def get_statistics(self) -> Dict:
        """Get statistics about the digraph."""
        return {
            'node_count': self.digraph.number_of_nodes(),
            'edge_count': self.digraph.number_of_edges(),
            'density': nx.density(self.digraph),
            'is_dag': nx.is_directed_acyclic_graph(self.digraph),
            'connected_components': nx.number_weakly_connected_components(self.digraph),
        }
    
    def get_toplevel_folders(self) -> List[str]:
        """Get toplevel folder nodes (folders at the root level)."""
        toplevel = []
        for node in self.digraph.nodes():
            # A toplevel folder is one without a parent
            if '/' not in node and node != 'root':
                toplevel.append(node)
        
        if 'root' in self.digraph.nodes():
            toplevel.insert(0, 'root')
        
        return sorted(toplevel)
    
    def get_folder_info(self, node_id: str) -> Dict:
        """Get information about a folder node."""
        if node_id not in self.digraph:
            return {}
        
        node_data = self.digraph.nodes[node_id]
        
        in_edges = list(self.digraph.in_edges(node_id, data=True))
        out_edges = list(self.digraph.out_edges(node_id, data=True))
        
        return {
            'node_id': node_id,
            'folder_path': node_data.get('folder_path'),
            'file_count': node_data.get('file_count', 0),
            'total_size': node_data.get('total_size', 0),
            'files': [f.name for f in node_data.get('files', [])],
            'incoming_dependencies': len(in_edges),
            'outgoing_dependencies': len(out_edges),
            'in_degree': self.digraph.in_degree(node_id),
            'out_degree': self.digraph.out_degree(node_id),
        }
