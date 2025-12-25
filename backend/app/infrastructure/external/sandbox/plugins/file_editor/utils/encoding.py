"""Encoding management for file operations."""

import functools
import inspect
import os
from pathlib import Path
from typing import TYPE_CHECKING

import charset_normalizer
from cachetools import LRUCache


if TYPE_CHECKING:
    from openhands.tools.file_editor.impl import FileEditor


class EncodingManager:
    """Manages file encodings across multiple operations to ensure consistency."""

    # Default maximum number of entries in the cache
    DEFAULT_MAX_CACHE_SIZE: int = 1000  # ~= 300 KB
    default_encoding: str
    confidence_threshold: float

    def __init__(self, max_cache_size=None):
        # Cache detected encodings to avoid repeated detection on the same file
        # Format: {path_str: (encoding, mtime)}
        self._encoding_cache: LRUCache[str, tuple[str, float]] = LRUCache(
            maxsize=max_cache_size or self.DEFAULT_MAX_CACHE_SIZE
        )
        # Default fallback encoding
        self.default_encoding = "utf-8"
        # Confidence threshold for encoding detection
        self.confidence_threshold = 0.9

    def detect_encoding(self, path: Path) -> str:
        """Detect the encoding of a file without handling caching logic.
        Args:
            path: Path to the file
        Returns:
            The detected encoding or default encoding if detection fails
        """
        # Handle non-existent files
        if not path.exists():
            return self.default_encoding

        # Read a sample of the file to detect encoding
        sample_size = min(os.path.getsize(path), 1024 * 1024)  # Max 1MB sample
        with open(path, "rb") as f:
            raw_data = f.read(sample_size)

        # Use charset_normalizer instead of chardet
        results = charset_normalizer.detect(raw_data)

        # Get the best match if any exists
        if (
            results
            and results["confidence"]
            and results["confidence"] > self.confidence_threshold
            and results["encoding"]
        ):
            encoding = results["encoding"]
            # Always use utf-8 instead of ascii for text files to support
            # non-ASCII characters. This ensures files initially containing only
            # ASCII can later accept non-ASCII content
            if encoding.lower() == "ascii":
                encoding = self.default_encoding
        else:
            encoding = self.default_encoding

        return encoding

    def get_encoding(self, path: Path) -> str:
        """Get encoding for a file, using cache or detecting if necessary.
        Args:
            path: Path to the file
        Returns:
            The encoding for the file
        """
        path_str = str(path)
        # If file doesn't exist, return default encoding
        if not path.exists():
            return self.default_encoding

        # Get current modification time
        current_mtime = os.path.getmtime(path)

        # Check cache for valid entry
        if path_str in self._encoding_cache:
            cached_encoding, cached_mtime = self._encoding_cache[path_str]
            if cached_mtime == current_mtime:
                return cached_encoding

        # No valid cache entry, detect encoding
        encoding = self.detect_encoding(path)

        # Cache the result with current modification time
        self._encoding_cache[path_str] = (encoding, current_mtime)
        return encoding


def with_encoding(method):
    """Decorator to handle file encoding for file operations.
    This decorator automatically detects and applies the correct encoding
    for file operations, ensuring consistency between read and write operations.
    Args:
        method: The method to decorate
    Returns:
        The decorated method
    """

    @functools.wraps(method)
    def wrapper(self: "FileEditor", path: Path, *args, **kwargs):
        # Skip encoding handling for directories
        if path.is_dir():
            return method(self, path, *args, **kwargs)

        # Check if the method accepts an encoding parameter
        sig = inspect.signature(method)
        accepts_encoding = "encoding" in sig.parameters

        if accepts_encoding:
            # For files that don't exist yet (like in 'create' command),
            # use the default encoding
            if not path.exists():
                if "encoding" not in kwargs:
                    kwargs["encoding"] = self._encoding_manager.default_encoding
            else:
                # Get encoding from the encoding manager for existing files
                encoding = self._encoding_manager.get_encoding(path)
                # Add encoding to kwargs if the method accepts it
                if "encoding" not in kwargs:
                    kwargs["encoding"] = encoding

        return method(self, path, *args, **kwargs)

    return wrapper
