"""
Example usage of the Blender documentation tool.

This script demonstrates how to use the tool programmatically.
"""

from pathlib import Path
from blender_doc.main import process_project


def example_basic():
    """Basic usage: generate full report."""
    project_folder = Path('./example_project')
    output_pdf = Path('./example_report.pdf')
    
    process_project(
        folder=project_folder,
        output_path=output_pdf,
        output_mode='full',
        verbose=True,
    )


def example_digraph_only():
    """Generate only the dependency digraph."""
    project_folder = Path('./example_project')
    output_pdf = Path('./digraph_report.pdf')
    
    process_project(
        folder=project_folder,
        output_path=output_pdf,
        output_mode='digraph_only',
        verbose=True,
    )


def example_details_only():
    """Generate only the file details."""
    project_folder = Path('./example_project')
    output_pdf = Path('./details_report.pdf')
    
    process_project(
        folder=project_folder,
        output_path=output_pdf,
        output_mode='details_only',
        verbose=True,
    )


def example_with_external_links():
    """Follow external links outside the project."""
    project_folder = Path('./example_project')
    output_pdf = Path('./report_with_externals.pdf')
    
    process_project(
        folder=project_folder,
        output_path=output_pdf,
        output_mode='full',
        follow_external=True,
        verbose=True,
    )


if __name__ == '__main__':
    # Uncomment to run examples
    # example_basic()
    pass
