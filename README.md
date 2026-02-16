# Blender Project Documentation Tool

A comprehensive documentation generator for Blender projects that scans your project folder, analyzes file dependencies, creates a digraph visualization, and generates a detailed PDF report.

## Features

- **Recursive Project Scanning**: Scans all files in your project folder and nested subfolders
- **Blend File Analysis**: Extracts dependencies from Blender files using headless Blender operations
- **Metadata Extraction**: Gathers detailed information about different file types:
  - Images: dimensions, format, color space
  - Audio: duration, channels, sample rate
  - Text files: line count, word count
  - 3D models: vertex counts, faces (for OBJ)
  - Blender files: object count, scene count, material count, vertex counts
- **Dependency Digraph**: Creates a visual graph showing how files depend on each other, grouped by folder hierarchy
- **Flexible PDF Export**:
  - **Full Report**: Digraph visualization + file inventory table + blend file details
  - **Digraph Only**: Just the dependency visualization
  - **Details Only**: Just the file inventory and blend file details
- **External Link Tracking**: Optionally follow and include external file references (optional CLI flag)

## Requirements

- Python 3.11+
- Blender 5.0+ (for blend file analysis)
- Dependencies: `bpy`, `networkx`, `reportlab`, `Pillow`, `pandas`, `matplotlib`

## Installation

```bash
pip install -e .
```

Or install with dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
blender-doc --folder /path/to/blender/project
```

This generates a full report PDF at `./blender_doc_report.pdf`

### Specify Output Path

```bash
blender-doc --folder /path/to/project --output my_report.pdf
```

### Output Modes

Generate only the dependency digraph:
```bash
blender-doc --folder /path/to/project --digraph-only
```

Generate only file details (no digraph):
```bash
blender-doc --folder /path/to/project --details-only
```

### Follow External Links

Include files referenced outside the project folder:
```bash
blender-doc --folder /path/to/project --follow-external
```

### Custom Blender Path

Specify a custom Blender executable location:
```bash
blender-doc --folder /path/to/project --blender-path /custom/path/to/blender
```

### Verbose Output

Enable detailed logging:
```bash
blender-doc --folder /path/to/project --verbose
```

## Project Structure

```
src/blender_doc/
├── __init__.py                 # Package initialization
├── main.py                     # Main orchestration logic
├── cli.py                      # Command-line interface
├── file_scanner.py             # Directory scanning and file discovery
├── file_processor.py           # Stack-based file processing orchestration
├── metadata_extractor.py       # Metadata extraction for various file types
├── blender_integration.py      # Headless Blender operations
├── digraph_builder.py          # Dependency graph construction
└── pdf_exporter.py             # PDF report generation
```

### Core Data Structures (data_structures.py)

- **FileEntry**: Represents a file with metadata and links to dependencies
- **BlendFileMetadata**: Blender-specific metadata (object counts, scenes, etc.)
- **MetadataStore**: Central store managing all file entries and indexing
- **LinkRegistry**: Tracks file dependencies and prevents circular links

## How It Works

### Processing Pipeline

1. **Scan**: Recursive scan of the project folder, creating FileEntry objects
2. **Process Stack**: Stack-based processing of files:
   - **Leaf nodes** (images, audio, text): Extract metadata and finalize
   - **Blend files**: Use Blender to extract dependencies and metadata
   - **New dependencies**: Add discovered files to processing stack
3. **Build Graph**: Create a digraph with nodes as folders, edges as dependencies
4. **Export PDF**: Generate report with selected content (digraph, details, or both)

### Dependency Detection

The tool discovers dependencies by:
- Parsing Blender files using headless Blender operations
- Identifying linked libraries, image textures, and external asset references
- Optionally following external file references outside the project folder (with `--follow-external`)

### Cycle Prevention

Built-in cycle detection prevents infinite loops when files have circular dependencies.

## Output Format

### Full Report PDF

**Page 1**: Dependency digraph visualization with statistics
**Page 2+**: File inventory table with columns:
- File Name
- Folder (relative path)
- Size (KB)
- Type (extension)
- Links (number of dependencies)
- Metadata (summary of content-specific info)

**Additional Pages**: Detailed Blender file information:
- Object count, scene count, material count, mesh count, vertex count
- List of dependencies

## Examples

### Example Commands

```bash
# Generate full report for a game project
blender-doc --folder ./game_assets --output game_docs.pdf

# Analyze a single Blender scene with external assets
blender-doc --folder ./my_scene --follow-external --output scene_analysis.pdf

# Generate digraph only for quick dependency overview
blender-doc --folder ./assets --digraph-only --output deps.pdf

# Detailed file inventory without visualization
blender-doc --folder ./textures --details-only --verbose --output inventory.pdf
```

## Troubleshooting

### Blender Not Found

If the tool can't auto-detect Blender:
```bash
blender-doc --folder ./project --blender-path /usr/bin/blender
```

### Blend File Analysis Fails

- Ensure Blender 5.0+ is installed and in PATH
- Check file permissions
- Verify blend files aren't corrupted
- Try with `--verbose` flag for more details

### Memory Issues with Large Projects

The tool processes files one at a time, so memory usage is generally low. For very large projects:
- Consider scanning in sections
- Use `--details-only` to skip digraph rendering

## Development

### Running Tests

```bash
pytest tests/
```

### Contributing

Contributions welcome! Areas for enhancement:
- Support for more file types
- Better digraph layout algorithms
- Interactive web-based report option
- Performance optimization for massive projects
- More detailed 3D model analysis

## License

MIT

## Author

Blender Doc Team
