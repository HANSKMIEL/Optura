import os
import logging
from typing import Tuple
from ..config import settings

logger = logging.getLogger(__name__)


class FileValidator:
    """Service for validating file uploads."""

    @staticmethod
    def validate_file(filename: str, size_bytes: int) -> Tuple[bool, str]:
        """
        Validate file based on extension, size, and other criteria.
        Returns (is_valid, error_message)
        """
        # Check file size
        max_size = settings.max_upload_size_mb * 1024 * 1024
        if size_bytes > max_size:
            return False, f"File size {size_bytes} bytes exceeds maximum {max_size} bytes"

        # Check file extension
        _, ext = os.path.splitext(filename)
        if ext.lower() not in settings.allowed_extensions:
            return False, f"File extension '{ext}' not allowed. Allowed: {', '.join(settings.allowed_extensions)}"

        # Check filename for suspicious patterns
        suspicious_patterns = ["../", "..\\", "/etc/", "c:\\", "~"]
        for pattern in suspicious_patterns:
            if pattern in filename.lower():
                return False, f"Suspicious pattern in filename: {pattern}"

        return True, ""

    @staticmethod
    def validate_content(content: bytes, mime_type: str) -> Tuple[bool, str]:
        """
        Validate file content for security issues.
        Returns (is_valid, error_message)
        """
        # Check for null bytes
        if b'\x00' in content:
            return False, "File contains null bytes"

        # Check content size
        if len(content) == 0:
            return False, "File is empty"

        # Basic validation based on mime type
        if mime_type.startswith("text/"):
            try:
                # Try to decode as text
                content.decode("utf-8")
            except UnicodeDecodeError:
                return False, "File claims to be text but contains invalid UTF-8"

        return True, ""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks."""
        # Get just the filename, no path
        filename = os.path.basename(filename)

        # Remove or replace problematic characters
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit filename length
        max_length = 255
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            name = name[:max_length - len(ext)]
            filename = name + ext

        return filename
