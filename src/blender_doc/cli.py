"""Command-line interface for Blender documentation tool."""

import argparse
from pathlib import Path
from typing import Optional


def create_parser() -> argparse.ArgumentParser:
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(
        description='Generate comprehensive documentation for Blender projects',
        epilog='Example: blender-doc --folder ./my_project --output report.pdf',
    )
    
    # Required arguments
    parser.add_argument(
        '--folder',
        required=True,
        type=Path,
        help='Root folder of the Blender project to scan',
    )
    
    # Optional arguments
    parser.add_argument(
        '-o', '--output',
        type=Path,
        default=Path.cwd() / 'blender_doc_report.pdf',
        help='Output PDF path (default: ./blender_doc_report.pdf)',
    )
    
    # Output mode (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--digraph-only',
        action='store_true',
        help='Export only the dependency digraph visualization',
    )
    mode_group.add_argument(
        '--details-only',
        action='store_true',
        help='Export only the file details spreadsheet and blend file information',
    )
    
    # Feature flags
    parser.add_argument(
        '--follow-external',
        action='store_true',
        help='Follow external links outside the project folder',
    )
    
    # Blender path
    parser.add_argument(
        '--blender-path',
        type=Path,
        default=None,
        help='Path to Blender executable (auto-detected if not specified)',
    )
    
    # Verbosity
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output',
    )
    
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """
    Validate parsed arguments.
    
    Args:
        args: Parsed arguments
    
    Raises:
        ValueError: If arguments are invalid
    """
    # Validate folder exists
    if not args.folder.exists():
        raise ValueError(f"Folder does not exist: {args.folder}")
    
    if not args.folder.is_dir():
        raise ValueError(f"Path is not a directory: {args.folder}")
    
    # Validate output directory exists (or can be created)
    output_dir = args.output.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate Blender path if specified
    if args.blender_path and not args.blender_path.exists():
        raise ValueError(f"Blender executable not found: {args.blender_path}")


def get_output_mode(args: argparse.Namespace) -> str:
    """Determine output mode from CLI arguments."""
    if args.digraph_only:
        return 'digraph_only'
    elif args.details_only:
        return 'details_only'
    else:
        return 'full'


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        validate_args(args)
    except ValueError as e:
        parser.error(str(e))
        return 1
    
    # Import main processing function
    from .main import process_project
    
    try:
        output_mode = get_output_mode(args)
        
        process_project(
            folder=args.folder,
            output_path=args.output,
            output_mode=output_mode,
            follow_external=args.follow_external,
            blender_path=args.blender_path,
            verbose=args.verbose,
        )
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
