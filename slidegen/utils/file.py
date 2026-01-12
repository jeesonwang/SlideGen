import hashlib
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO

from loguru import logger

from slidegen.core.constants import UPLOAD_DIR
from slidegen.exceptions import FileTypeError


def _format_size_mb(size_bytes: int) -> str:
    """Format byte size as MB string with 2 decimal places."""
    return f"{size_bytes / 1024 / 1024:.2f}MB"


class FileManager:
    """Manage file upload and retrieval"""

    ALLOWED_EXTENSIONS = {
        ".docx",
        ".doc",
        ".xlsx",
        ".xls",
        ".html",
        ".htm",
        ".txt",
        ".md",
        ".pdf",
    }

    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-excel",  # .xls
        "text/html",  # .html
        "text/plain",  # .txt
        "text/markdown",  # .md
        "application/pdf",  # .pdf
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB

    def __init__(self, upload_dir: str | Path | None = None):
        self.upload_dir = Path(upload_dir) if upload_dir else Path(UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileManager initialized with upload directory: {self.upload_dir}")

    def generate_file_id(self) -> str:
        """Generate a unique file ID in UUID format."""
        return str(uuid.uuid4())

    def validate_file_type(self, filename: str, content: bytes | None = None) -> bool:
        """
        Validate file type by extension.

        Raises:
            FileTypeError: if file type is not supported
        """
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise FileTypeError(
                f"Unsupported file type: {ext}. Supported types: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        return True

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize file name to prevent path traversal attacks."""
        name = Path(filename).name
        unsafe_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
        for char in unsafe_chars:
            name = name.replace(char, "_")
        return name or "unnamed_file"

    def _validate_file_size(self, file_size: int) -> None:
        """
        Validate file size against MAX_FILE_SIZE limit.

        Raises:
            ValueError: if file size exceeds limit
        """
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File size ({_format_size_mb(file_size)}) exceeds limit ({_format_size_mb(self.MAX_FILE_SIZE)})"
            )

    def _validate_file_size_before_read(self, file_content: BinaryIO) -> None:
        """
        Validate file size before reading by seeking to end.
        Silently skips validation if the stream does not support seeking.

        Raises:
            ValueError: if file size exceeds limit
        """
        try:
            file_content.seek(0, 2)
            file_size = file_content.tell()
            file_content.seek(0)
            self._validate_file_size(file_size)
        except (OSError, AttributeError):
            pass  # Non-seekable stream; validation deferred to after read

    def _read_and_validate_content(self, file_content: BinaryIO, filename: str) -> tuple[bytes, str]:
        """
        Read file content, validate size and type.

        Returns:
            Tuple of (content bytes, sanitized filename)

        Raises:
            FileTypeError: if file type not supported
            ValueError: if file size exceeds limit
        """
        safe_filename = self.sanitize_filename(filename)
        self._validate_file_size_before_read(file_content)

        content = file_content.read()
        self._validate_file_size(len(content))
        self.validate_file_type(safe_filename, content)

        return content, safe_filename

    def save_uploaded_file(
        self,
        file_content: BinaryIO,
        filename: str,
        user_id: str | None = None,
    ) -> tuple[str, str]:
        """
        Save uploaded file.

        Returns:
            (file_id, file_path) tuple

        Raises:
            FileTypeError: if file type not supported
            ValueError: if file size exceeds limit
        """
        content, safe_filename = self._read_and_validate_content(file_content, filename)
        file_id = self.generate_file_id()

        if user_id:
            base_dir = self.upload_dir / str(user_id)
            base_dir.mkdir(parents=True, exist_ok=True)
        else:
            base_dir = self.upload_dir

        file_path = base_dir / f"{file_id}_{safe_filename}"
        file_path.write_bytes(content)

        logger.info(f"File saved: {file_path} (size: {len(content)} bytes)")
        return file_id, str(file_path)

    def _find_file_in_dir(self, directory: Path, file_id: str) -> str | None:
        """Find a file by ID prefix in the given directory."""
        if not directory.exists():
            return None
        for file_path in directory.glob(f"{file_id}_*"):
            if file_path.is_file():
                return str(file_path)
        return None

    def get_file_path(self, file_id: str, user_id: str | None = None) -> str | None:
        """Get file path by file ID. Returns None if not found."""
        search_dirs = [self.upload_dir / str(user_id)] if user_id else []
        search_dirs.append(self.upload_dir)

        for search_dir in search_dirs:
            if result := self._find_file_in_dir(search_dir, file_id):
                return result

        logger.warning(f"File not found: {file_id}")
        return None

    def _delete_file_at_path(self, file_path: str) -> bool:
        """Attempt to delete a file at the given path."""
        try:
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def delete_file(self, file_id: str, user_id: str | None = None) -> bool:
        """Delete file by ID. Returns True if successfully deleted."""
        file_path = self.get_file_path(file_id, user_id)
        if file_path is None:
            return False
        return self._delete_file_at_path(file_path)

    def _list_files_in_dir(
        self, directory: Path, context_key: str, context_value: str
    ) -> list[dict[str, Any]]:
        """
        List all files in a directory with metadata.

        Args:
            directory: directory to list files from
            context_key: key name for the context identifier (e.g., "user_id" or "session_id")
            context_value: value for the context identifier
        """
        if not directory.exists() or not directory.is_dir():
            return []

        files: list[dict[str, Any]] = []
        sorted_paths = sorted(directory.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)

        for file_path in sorted_paths:
            if not file_path.is_file():
                continue

            parts = file_path.name.split("_", 1)
            file_id = parts[0]
            original_filename = parts[1] if len(parts) > 1 else file_path.name
            stat = file_path.stat()

            files.append({
                "file_id": file_id,
                "filename": original_filename,
                "file_size": stat.st_size,
                "file_path": str(file_path),
                "upload_time": datetime.fromtimestamp(stat.st_mtime),
                context_key: context_value,
            })

        return files

    def list_user_files(self, user_id: str) -> list[dict[str, Any]]:
        """List all files uploaded by a specific user."""
        user_dir = self.upload_dir / str(user_id)
        files = self._list_files_in_dir(user_dir, "user_id", str(user_id))
        if not files:
            logger.info(f"No files found for user {user_id}")
        return files

    def cleanup_old_files(self, days: int = 7) -> int:
        """Clean up files older than the specified number of days."""
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for file_path in self.upload_dir.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"Deleted old file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete old file {file_path}: {e}")

        logger.info(f"Cleanup completed: {deleted_count} files deleted")
        return deleted_count

    def get_file_hash(self, file_path: str) -> str:
        """Calculate the SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def validate_total_size(self, file_sizes: list[int]) -> bool:
        """
        Validate that total file size is within limit.

        Raises:
            ValueError: if total size exceeds limit
        """
        total_size = sum(file_sizes)
        if total_size > self.MAX_TOTAL_SIZE:
            raise ValueError(
                f"Total file size ({_format_size_mb(total_size)}) exceeds limit ({_format_size_mb(self.MAX_TOTAL_SIZE)})"
            )
        return True

    # ========== Session-Scoped Methods ==========

    def _cleanup_empty_directory(self, directory: Path, was_created: bool) -> None:
        """Remove directory if it was newly created and is empty."""
        if not was_created or not directory.exists():
            return
        try:
            if not any(directory.iterdir()):
                directory.rmdir()
                logger.info(f"Cleaned up empty directory after failure: {directory}")
        except Exception as e:
            logger.warning(f"Failed to cleanup directory {directory}: {e}")

    def save_uploaded_file_to_session(
        self,
        file_content: BinaryIO,
        filename: str,
        session_id: str,
        user_id: str | None = None,
    ) -> tuple[str, str]:
        """
        Save uploaded file to session directory.

        Storage path: {UPLOAD_DIR}/{session_id}/{file_id}_{filename}

        Returns:
            (file_id, file_path) tuple

        Raises:
            FileTypeError: if file type not supported
            ValueError: if file size exceeds limit
        """
        content, safe_filename = self._read_and_validate_content(file_content, filename)
        file_id = self.generate_file_id()

        session_dir = self.upload_dir / str(session_id)
        session_dir_created = not session_dir.exists()

        try:
            session_dir.mkdir(parents=True, exist_ok=True)
            file_path = session_dir / f"{file_id}_{safe_filename}"
            file_path.write_bytes(content)

            logger.info(f"File saved to session {session_id}: {file_path} (size: {len(content)} bytes)")
            return file_id, str(file_path)
        except Exception:
            self._cleanup_empty_directory(session_dir, session_dir_created)
            raise

    def get_session_file_path(self, file_id: str, session_id: str) -> str | None:
        """Get file path from session directory. Returns None if not found."""
        session_dir = self.upload_dir / str(session_id)
        if not session_dir.exists():
            logger.warning(f"Session directory not found: {session_id}")
            return None

        if result := self._find_file_in_dir(session_dir, file_id):
            return result

        logger.warning(f"File not found in session {session_id}: {file_id}")
        return None

    def delete_session_file(self, file_id: str, session_id: str) -> bool:
        """Delete file from session directory. Returns True if successfully deleted."""
        file_path = self.get_session_file_path(file_id, session_id)
        if file_path is None:
            return False
        return self._delete_file_at_path(file_path)

    def delete_session_directory(self, session_id: str) -> int:
        """Delete entire session directory and all files. Returns number of files deleted."""
        session_dir = self.upload_dir / str(session_id)
        if not session_dir.exists():
            logger.info(f"Session directory does not exist: {session_id}")
            return 0

        count = 0
        for file_path in session_dir.glob("*"):
            if file_path.is_file():
                try:
                    os.remove(file_path)
                    count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")

        # Remove directory if empty
        try:
            session_dir.rmdir()
            logger.info(f"Deleted session directory: {session_dir}")
        except Exception as e:
            logger.warning(f"Could not remove directory {session_dir}: {e}")

        logger.info(f"Deleted {count} files from session {session_id}")
        return count

    def list_session_files(self, session_id: str) -> list[dict[str, Any]]:
        """List all files in a specific session."""
        session_dir = self.upload_dir / str(session_id)
        files = self._list_files_in_dir(session_dir, "session_id", str(session_id))
        if not files:
            logger.info(f"No files found for session {session_id}")
        return files


file_manager = FileManager()
