"""PDF export functionality - generates PDF reports."""

from pathlib import Path
from typing import List, Literal, Optional
import io
import tempfile

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak, Spacer
from reportlab.platypus import Image as RLImage
import networkx as nx
import matplotlib.pyplot as plt

from .data_structures import FileEntry, MetadataStore
from .digraph_builder import DigraphBuilder


OutputMode = Literal['full', 'digraph_only', 'details_only']


class PDFExporter:
    """Exports project documentation to PDF."""
    
    def __init__(
        self,
        metadata_store: MetadataStore,
        digraph_builder: DigraphBuilder,
        output_path: Path,
        output_mode: OutputMode = 'full',
    ):
        """
        Initialize PDF exporter.
        
        Args:
            metadata_store: Store with all file metadata
            digraph_builder: Builder with the digraph
            output_path: Path to save PDF
            output_mode: 'full' (default), 'digraph_only', or 'details_only'
        """
        self.metadata_store = metadata_store
        self.digraph_builder = digraph_builder
        self.output_path = Path(output_path)
        self.output_mode = output_mode
        self.temp_files = []
    
    def export(self) -> None:
        """Generate and save the PDF report."""
        try:
            # Create document
            doc = SimpleDocTemplate(
                str(self.output_path),
                pagesize=letter,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch,
                leftMargin=0.5*inch,
                rightMargin=0.5*inch,
            )
            
            # Build content based on output mode
            content = []
            
            if self.output_mode in ('full', 'digraph_only'):
                content.extend(self._build_digraph_section())
            
            if self.output_mode in ('full', 'details_only'):
                if self.output_mode == 'full':
                    content.append(PageBreak())
                content.extend(self._build_details_section())
            
            # Build PDF
            doc.build(content)
            print(f"PDF exported to: {self.output_path}")
        
        finally:
            # Clean up temp files
            self._cleanup_temp_files()
    
    def _build_digraph_section(self) -> List:
        """Build the digraph visualization section."""
        content = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1f77b4'),
            spaceAfter=30,
        )
        content.append(Paragraph('Project Dependency Graph', title_style))
        content.append(Spacer(1, 0.2*inch))
        
        # Generate digraph visualization
        digraph = self.digraph_builder.get_digraph()
        
        if digraph.number_of_nodes() > 0:
            # Create image from digraph
            img_path = self._render_digraph_image(digraph)
            
            if img_path:
                # Track temp file for cleanup
                self.temp_files.append(img_path)
                
                # Add image
                img = RLImage(
                    img_path,
                    width=7*inch,
                    height=5*inch,
                    kind='proportional',
                )
                content.append(img)
        else:
            content.append(Paragraph('No dependencies found', styles['Normal']))
        
        # Add statistics
        content.append(Spacer(1, 0.3*inch))
        stats = self.digraph_builder.get_statistics()
        stats_text = f"Files: {stats['file_count']} | Links: {stats['link_count']} | " \
                     f"Density: {stats['density']:.3f}"
        content.append(Paragraph(stats_text, styles['Normal']))
        
        return content
    
    def _build_details_section(self) -> List:
        """Build the file details spreadsheet section."""
        content = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1f77b4'),
            spaceAfter=30,
        )
        content.append(Paragraph('File Inventory', title_style))
        content.append(Spacer(1, 0.2*inch))
        
        # Build table data
        entries = self.metadata_store.get_all_entries()
        
        table_data = [
            ['File Name', 'Folder', 'Size (KB)', 'Type', 'Links', 'Metadata']
        ]
        
        for entry in sorted(entries, key=lambda e: str(e.path)):
            # Format metadata
            metadata_summary = self._format_metadata_summary(entry)
            
            # Format size
            size_kb = entry.size / 1024 if entry.size > 0 else 0
            
            table_data.append([
                entry.name,
                self.metadata_store.get_relative_path(entry),
                f"{size_kb:.1f}",
                entry.file_type,
                str(len(entry.links)),
                metadata_summary,
            ])
        
        # Create table
        table = Table(table_data, colWidths=[1.2*inch, 1.5*inch, 0.8*inch, 0.7*inch, 0.6*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f9f9f9')]),
        ]))
        
        content.append(table)
        
        # Add blend file details if any exist
        blend_files = [e for e in entries if e.file_type == 'blend']
        if blend_files:
            content.append(PageBreak())
            content.extend(self._build_blend_details_section(blend_files))
        
        return content
    
    def _build_blend_details_section(self, blend_files: List[FileEntry]) -> List:
        """Build detailed Blender file information section."""
        content = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=HexColor('#1f77b4'),
            spaceAfter=20,
        )
        content.append(Paragraph('Blender File Details', title_style))
        
        for blend_file in blend_files:
            content.append(Spacer(1, 0.2*inch))
            
            # File name
            file_title = ParagraphStyle(
                'FileTitle',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=HexColor('#2ca02c'),
            )
            content.append(Paragraph(f"File: {blend_file.name}", file_title))
            
            # Metadata table
            blend_meta = blend_file.metadata.get('blend', {})
            
            details_data = [
                ['Property', 'Value'],
                ['Objects', str(blend_meta.get('object_count', 'N/A'))],
                ['Scenes', str(blend_meta.get('scene_count', 'N/A'))],
                ['Materials', str(blend_meta.get('material_count', 'N/A'))],
                ['Meshes', str(blend_meta.get('mesh_count', 'N/A'))],
                ['Total Vertices', str(blend_meta.get('total_vertex_count', 'N/A'))],
            ]
            
            details_table = Table(details_data, colWidths=[2*inch, 2*inch])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2ca02c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#cccccc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f9f9f9')]),
            ]))
            
            content.append(details_table)
            
            # Dependencies
            if len(blend_file.links) > 0:
                content.append(Spacer(1, 0.15*inch))
                deps_text = f"<b>Dependencies ({len(blend_file.links)}):</b> " + \
                           ", ".join([l.name for l in blend_file.links[:10]])
                if len(blend_file.links) > 10:
                    deps_text += f" ... and {len(blend_file.links) - 10} more"
                content.append(Paragraph(deps_text, styles['Normal']))
        
        return content
    
    def _format_metadata_summary(self, entry: FileEntry) -> str:
        """Format metadata into a brief summary string."""
        if not entry.metadata:
            return '-'
        
        parts = []
        
        # Image metadata
        if 'dimensions' in entry.metadata:
            parts.append(f"{entry.metadata['dimensions']}")
        
        # Audio metadata
        if 'duration_seconds' in entry.metadata:
            parts.append(f"{entry.metadata['duration_seconds']}s")
        if 'channels' in entry.metadata:
            parts.append(f"{entry.metadata['channels']}ch")
        
        # Text metadata
        if 'line_count' in entry.metadata:
            parts.append(f"{entry.metadata['line_count']} lines")
        
        # Model metadata
        if 'vertices' in entry.metadata:
            parts.append(f"{entry.metadata['vertices']} verts")
        
        # Blend metadata
        if 'blend' in entry.metadata:
            blend_meta = entry.metadata['blend']
            if blend_meta.get('object_count'):
                parts.append(f"{blend_meta['object_count']} objs")
        
        return ' | '.join(parts) if parts else '-'
    
    def _render_digraph_image(self, digraph: nx.DiGraph) -> Optional[str]:
        """
        Render the digraph as an image.
        
        Returns:
            Path to temporary image file, or None if failed
        """
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=(14, 10), dpi=100)
            
            # Use hierarchical layout with more spacing
            if digraph.number_of_nodes() > 0:
                pos = nx.spring_layout(digraph, k=3, iterations=80, seed=42)
            else:
                pos = {}
            
            # Draw nodes with colors by file type
            node_colors = []
            node_sizes = []
            file_type_colors = {
                'blend': '#FF6B35',  # Orange for blend files
                'png': '#004E89',    # Blue for images
                'jpg': '#004E89',
                'jpeg': '#004E89',
                'exr': '#004E89',
                'hdr': '#004E89',
                'wav': '#1F77B4',    # Light blue for audio
                'mp3': '#1F77B4',
                'flac': '#1F77B4',
                'txt': '#2CA02C',    # Green for text
                'json': '#2CA02C',
                'csv': '#2CA02C',
                'obj': '#9467BD',    # Purple for 3D models
                'fbx': '#9467BD',
                'gltf': '#9467BD',
            }
            
            for node in digraph.nodes():
                file_type = digraph.nodes[node].get('file_type', 'unknown')
                color = file_type_colors.get(file_type, '#D3D3D3')
                node_colors.append(color)
                
                # Size nodes by file size (with minimum)
                size = max(300, digraph.nodes[node].get('size', 1000) / 10000)
                node_sizes.append(size)
            
            nx.draw_networkx_nodes(
                digraph,
                pos,
                node_color=node_colors,
                node_size=node_sizes,
                alpha=0.8,
                ax=ax,
            )
            
            # Draw edges
            nx.draw_networkx_edges(
                digraph,
                pos,
                edge_color='gray',
                arrows=True,
                arrowsize=20,
                arrowstyle='->',
                connectionstyle='arc3,rad=0.1',
                ax=ax,
                width=1.5,
            )
            
            # Draw labels
            nx.draw_networkx_labels(
                digraph,
                pos,
                font_size=8,
                font_weight='bold',
                ax=ax,
            )
            
            ax.set_title('Project Dependency Graph (File-Level)', fontsize=14, fontweight='bold')
            ax.axis('off')
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_file.close()
            
            fig.savefig(temp_file.name, bbox_inches='tight', dpi=100, facecolor='white')
            plt.close(fig)
            
            return temp_file.name
        
        except Exception as e:
            print(f"Warning: Failed to render digraph image: {e}")
            return None
    
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                Path(temp_file).unlink()
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_file}: {e}")
