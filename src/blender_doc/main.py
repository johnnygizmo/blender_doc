"""Main entry point for Blender project documentation tool."""

import sys
from pathlib import Path
from typing import Optional, Literal

from .file_scanner import FileScanner
from .file_processor import FileProcessor
from .metadata_extractor import MetadataExtractor
from .blender_integration import BlenderIntegration
from .digraph_builder import DigraphBuilder
from .pdf_exporter import PDFExporter
from .data_structures import MetadataStore, LinkRegistry


def process_project(
    folder: Path,
    output_path: Path,
    output_mode: Literal['full', 'digraph_only', 'details_only'] = 'full',
    follow_external: bool = False,
    blender_path: Optional[Path] = None,
    verbose: bool = False,
) -> None:
    """
    Process a Blender project and generate documentation.
    
    Args:
        folder: Root folder of the project
        output_path: Path to save the PDF
        output_mode: 'full' (default), 'digraph_only', or 'details_only'
        follow_external: Whether to follow external links outside the folder
        blender_path: Optional path to Blender executable
        verbose: Enable verbose output
    """
    folder = Path(folder)
    output_path = Path(output_path)
    
    if verbose:
        print(f"Starting documentation generation...", file=sys.stderr)
        print(f"Project folder: {folder}", file=sys.stderr)
        print(f"Output mode: {output_mode}", file=sys.stderr)
        print(f"Follow external links: {follow_external}", file=sys.stderr)
    
    # Initialize data structures
    metadata_store = MetadataStore()
    link_registry = LinkRegistry()
    metadata_store.set_root_folder(folder)
    
    # Step 1: Scan filesystem
    if verbose:
        print("Step 1: Scanning filesystem...", file=sys.stderr)
    
    scanner = FileScanner(folder)
    entries, processing_stack = scanner.scan(recursive=True)
    
    for entry in entries:
        metadata_store.add_entry(entry)
    
    if verbose:
        print(f"  Found {len(entries)} files", file=sys.stderr)
    
    # Step 2: Initialize Blender integration if available
    blender_integration = None
    if verbose:
        print("Step 2: Initializing Blender integration...", file=sys.stderr)
    
    try:
        blender_integration = BlenderIntegration(str(blender_path) if blender_path else None)
        if verbose:
            print(f"  Blender integration available", file=sys.stderr)
    except RuntimeError as e:
        if verbose:
            print(f"  Blender integration not available: {e}", file=sys.stderr)
        print(f"Warning: {e}", file=sys.stderr)
    
    # Step 3: Process file stack
    if verbose:
        print("Step 3: Processing file stack...", file=sys.stderr)
    
    processor = FileProcessor(
        root_folder=folder,
        metadata_store=metadata_store,
        link_registry=link_registry,
        blender_integration=blender_integration,
        follow_external=follow_external,
    )
    
    output_list = processor.process_stack(processing_stack)
    
    if verbose:
        print(f"  Processed {len(output_list)} files", file=sys.stderr)
    
    # Step 4: Build digraph
    if verbose:
        print("Step 4: Building dependency digraph...", file=sys.stderr)
    
    digraph_builder = DigraphBuilder(metadata_store, link_registry)
    digraph = digraph_builder.build_by_folder_hierarchy(folder)
    
    stats = digraph_builder.get_statistics()
    if verbose:
        print(f"  Digraph: {stats['file_count']} files, {stats['link_count']} links",
              file=sys.stderr)
    
    # Step 5: Export to PDF
    if verbose:
        print("Step 5: Exporting to PDF...", file=sys.stderr)
    
    exporter = PDFExporter(
        metadata_store=metadata_store,
        digraph_builder=digraph_builder,
        output_path=output_path,
        output_mode=output_mode,
    )
    
    exporter.export()
    
    if verbose:
        print(f"Successfully generated: {output_path}", file=sys.stderr)
    
    # Summary
    print(f"\n=== Documentation Report ===")
    print(f"Output: {output_path}")
    print(f"Files scanned: {len(entries)}")
    print(f"Files in graph: {stats['file_count']}")
    print(f"Dependencies found: {stats['link_count']}")
    print(f"Mode: {output_mode}")


if __name__ == '__main__':
    from .cli import main
    sys.exit(main())
