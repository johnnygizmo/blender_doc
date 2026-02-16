"""Metadata extraction for different file types."""

import os
from pathlib import Path
from typing import Dict, Any

try:
    from PIL import Image
except ImportError:
    Image = None


class MetadataExtractor:
    """Extracts metadata from various file types."""
    
    @staticmethod
    def extract(file_path: Path, file_type: str) -> Dict[str, Any]:
        """
        Extract metadata for a file based on its type.
        
        Args:
            file_path: Path to the file
            file_type: File extension/type
        
        Returns:
            Dictionary with metadata key-value pairs
        """
        metadata = {}
        
        # Image metadata
        if file_type in ('jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'gif', 'webp'):
            metadata = MetadataExtractor._extract_image_metadata(file_path)
        
        # Audio metadata
        elif file_type in ('mp3', 'wav', 'flac', 'aac', 'ogg', 'aiff'):
            metadata = MetadataExtractor._extract_audio_metadata(file_path)
        
        # Text metadata
        elif file_type in ('txt', 'md', 'rst', 'csv', 'json', 'xml', 'yaml', 'yml'):
            metadata = MetadataExtractor._extract_text_metadata(file_path)
        
        # 3D model metadata
        elif file_type in ('obj', 'fbx', 'usd', 'usda', 'glb', 'gltf'):
            metadata = MetadataExtractor._extract_model_metadata(file_path)
        
        # EXR/HDR image metadata
        elif file_type in ('exr', 'hdr'):
            metadata = MetadataExtractor._extract_hdr_metadata(file_path)
        
        return metadata
    
    @staticmethod
    def _extract_image_metadata(file_path: Path) -> Dict[str, Any]:
        """Extract metadata from image files."""
        metadata = {}
        
        if Image is None:
            return metadata
        
        try:
            with Image.open(file_path) as img:
                metadata['format'] = img.format
                metadata['dimensions'] = f"{img.width}x{img.height}"
                metadata['width'] = img.width
                metadata['height'] = img.height
                metadata['mode'] = img.mode
                metadata['color_space'] = img.mode
                
                if hasattr(img, 'n_frames'):
                    metadata['frame_count'] = img.n_frames
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    @staticmethod
    def _extract_audio_metadata(file_path: Path) -> Dict[str, Any]:
        """Extract metadata from audio files."""
        metadata = {}
        
        # Try to use wave module for WAV files
        if file_path.suffix.lower() == '.wav':
            try:
                import wave
                with wave.open(file_path, 'rb') as wav_file:
                    n_channels = wav_file.getnchannels()
                    sample_width = wav_file.getsampwidth()
                    frame_rate = wav_file.getframerate()
                    n_frames = wav_file.getnframes()
                    
                    metadata['channels'] = n_channels
                    metadata['sample_rate'] = frame_rate
                    metadata['bit_depth'] = sample_width * 8
                    duration_seconds = n_frames / frame_rate if frame_rate > 0 else 0
                    metadata['duration_seconds'] = round(duration_seconds, 2)
            except Exception as e:
                metadata['error'] = str(e)
        else:
            # For other audio formats, try using mutagen if available
            try:
                from mutagen.wave import WAVE
                from mutagen.flac import FLAC
                from mutagen.mp3 import MP3
                from mutagen.oggvorbis import OggVorbis
                
                if file_path.suffix.lower() == '.flac':
                    audio = FLAC(file_path)
                    if audio.info:
                        metadata['channels'] = audio.info.channels
                        metadata['sample_rate'] = audio.info.sample_rate
                        metadata['duration_seconds'] = round(audio.info.length, 2)
                elif file_path.suffix.lower() == '.mp3':
                    audio = MP3(file_path)
                    if audio.info:
                        metadata['bitrate'] = audio.info.bitrate
                        metadata['sample_rate'] = audio.info.sample_rate
                        metadata['duration_seconds'] = round(audio.info.length, 2)
                elif file_path.suffix.lower() == '.ogg':
                    audio = OggVorbis(file_path)
                    if audio.info:
                        metadata['channels'] = audio.info.channels
                        metadata['sample_rate'] = audio.info.sample_rate
                        metadata['duration_seconds'] = round(audio.info.length, 2)
            except ImportError:
                pass
            except Exception as e:
                metadata['error'] = str(e)
        
        return metadata
    
    @staticmethod
    def _extract_text_metadata(file_path: Path) -> Dict[str, Any]:
        """Extract metadata from text files."""
        metadata = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                metadata['line_count'] = len(lines)
                metadata['encoding'] = 'utf-8'
                
                # Count words (rough estimate)
                total_words = sum(len(line.split()) for line in lines)
                metadata['word_count'] = total_words
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    @staticmethod
    def _extract_model_metadata(file_path: Path) -> Dict[str, Any]:
        """Extract metadata from 3D model files."""
        metadata = {}
        
        file_type = file_path.suffix.lower().lstrip('.')
        
        # OBJ file metadata
        if file_type == 'obj':
            metadata = MetadataExtractor._parse_obj(file_path)
        
        # For FBX, USD, GLB/GLTF - basic parsing without external dependencies
        # This is simplified; production would use dedicated libraries
        else:
            # Just indicate file type for now
            metadata['model_type'] = file_type
        
        return metadata
    
    @staticmethod
    def _parse_obj(file_path: Path) -> Dict[str, Any]:
        """Parse OBJ file for metadata."""
        metadata = {'model_type': 'obj'}
        
        try:
            vertices = 0
            faces = 0
            normals = 0
            textures = 0
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('v '):
                        vertices += 1
                    elif line.startswith('vn '):
                        normals += 1
                    elif line.startswith('vt '):
                        textures += 1
                    elif line.startswith('f '):
                        faces += 1
            
            metadata['vertices'] = vertices
            metadata['faces'] = faces
            metadata['normals'] = normals
            metadata['texture_coords'] = textures
        except Exception as e:
            metadata['error'] = str(e)
        
        return metadata
    
    @staticmethod
    def _extract_hdr_metadata(file_path: Path) -> Dict[str, Any]:
        """Extract metadata from HDR/EXR files."""
        metadata = {}
        
        # Try using PIL for basic HDR support
        if Image is not None:
            try:
                with Image.open(file_path) as img:
                    metadata['format'] = img.format
                    metadata['dimensions'] = f"{img.width}x{img.height}"
                    metadata['width'] = img.width
                    metadata['height'] = img.height
            except Exception as e:
                metadata['error'] = str(e)
        
        return metadata
