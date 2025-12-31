import hashlib
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO

from loguru import logger

from slidegen.core.constants import UPLOAD_DIR
from slidegen.exceptions import FileTypeError


class FileManager:
    """Manage file upload and retrieval"""

    # allowed file extensions
    ALLOWED_EXTENSIONS = {
        ".docx",
        ".doc",
        ".xlsx",
        ".xls",
        ".html",
        ".htm",
        ".txt",
        ".md",
    }

    # allowed MIME types
    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-excel",  # .xls
        "text/html",  # .html
        "text/plain",  # .txt
        "text/markdown",  # .md
    }

    # max file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # max total size (50MB)
    MAX_TOTAL_SIZE = 50 * 1024 * 1024

    def __init__(self, upload_dir: str | Path | None = None):
        """
        Initialize file manager

        Args:
            upload_dir: upload directory, default is UPLOAD_DIR
        """
        if upload_dir is None:
            upload_dir = UPLOAD_DIR

        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileManager initialized with upload directory: {self.upload_dir}")

    def generate_file_id(self) -> str:
        """
        Generate a unique file ID

        Returns:
            UUID format file ID
        """
        return str(uuid.uuid4())

    def validate_file_type(self, filename: str, content: bytes | None = None) -> bool:
        """
        Validate file type

        Args:
            filename: file name
            content: file content (optional, used for more precise validation)

        Returns:
            bool: whether the file type is allowed

        Raises:
            FileTypeError: file type not supported
        """
        # check file extension
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise FileTypeError(f"Unsupported file type: {ext}. Supported types: {', '.join(self.ALLOWED_EXTENSIONS)}")

        return True

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize file name, prevent path traversal attack

        Args:
            filename: original file name

        Returns:
            sanitized file name
        """
        # only keep file name, remove directory path
        filename = Path(filename).name

        # remove unsafe characters
        unsafe_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
        for char in unsafe_chars:
            filename = filename.replace(char, "_")

        # ensure file name is not empty and valid
        if not filename:
            filename = "unnamed_file"

        return filename

    def save_uploaded_file(
        self,
        file_content: BinaryIO,
        filename: str,
        user_id: str | None = None,
    ) -> tuple[str, str]:
        """
        Save uploaded file

        Args:
            file_content: file content stream
            filename: original file name
            user_id: user ID (optional)

        Returns:
            (file_id, file_path) tuple

        Raises:
            FileTypeError: file type not supported
            ValueError: file size exceeds limit
        """
        # sanitize file name
        safe_filename = self.sanitize_filename(filename)

        # read file content
        content = file_content.read()
        file_size = len(content)

        # validate file size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds limit ({self.MAX_FILE_SIZE / 1024 / 1024:.2f}MB)"
            )

        # validate file type
        self.validate_file_type(safe_filename, content)

        # generate file ID
        file_id = self.generate_file_id()

        # create user-specific directory if user_id is provided
        if user_id:
            user_dir = self.upload_dir / str(user_id)
            user_dir.mkdir(parents=True, exist_ok=True)
            base_dir = user_dir
        else:
            base_dir = self.upload_dir

        # build file path: {file_id}_{original_filename}
        final_filename = f"{file_id}_{safe_filename}"
        file_path = base_dir / final_filename

        # save file
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"File saved: {file_path} (size: {file_size} bytes)")

        return file_id, str(file_path)

    def get_file_path(self, file_id: str, user_id: str | None = None) -> str | None:
        """
        Get file path by file ID

        Args:
            file_id: file ID
            user_id: user ID (optional)

        Returns:
            file path if found, otherwise None
        """
        # search directories
        search_dirs = []
        if user_id:
            search_dirs.append(self.upload_dir / str(user_id))
        search_dirs.append(self.upload_dir)

        # search files in directories
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for file_path in search_dir.glob(f"{file_id}_*"):
                if file_path.is_file():
                    return str(file_path)

        logger.warning(f"File not found: {file_id}")
        return None

    def delete_file(self, file_id: str, user_id: str | None = None) -> bool:
        """
        Delete file

        Args:
            file_id: file ID
            user_id: user ID (optional)

        Returns:
            whether the file was successfully deleted
        """
        file_path = self.get_file_path(file_id, user_id)
        if file_path is None:
            return False

        try:
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def list_user_files(self, user_id: str) -> list[dict[str, Any]]:
        """
        List all files uploaded by a specific user.

        Args:
            user_id: user ID

        Returns:
            list of file metadata dicts
        """
        user_dir = self.upload_dir / str(user_id)
        if not user_dir.exists() or not user_dir.is_dir():
            logger.info(f"No files found for user {user_id}")
            return []

        files: list[dict[str, Any]] = []
        for file_path in sorted(user_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
            if not file_path.is_file():
                continue

            parts = file_path.name.split("_", 1)
            file_id = parts[0]
            original_filename = parts[1] if len(parts) > 1 else file_path.name

            stat = file_path.stat()

            files.append(
                {
                    "file_id": file_id,
                    "filename": original_filename,
                    "file_size": stat.st_size,
                    "file_path": str(file_path),
                    "upload_time": datetime.fromtimestamp(stat.st_mtime),
                    "user_id": str(user_id),
                }
            )

        return files

    def cleanup_old_files(self, days: int = 7) -> int:
        """
        Clean up expired files

        Args:
            days: number of days to keep files, files older than this will be deleted

        Returns:
            number of files deleted
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for file_path in self.upload_dir.rglob("*"):
            if not file_path.is_file():
                continue

            try:
                # get file modification time
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
        """
        Calculate the SHA256 hash of a file

        Args:
            file_path: file path

        Returns:
            SHA256 hash of the file
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def validate_total_size(self, file_sizes: list[int]) -> bool:
        """
        Validate total file size

        Args:
            file_sizes: list of file sizes in bytes

        Returns:
            whether the total size is within the limit

        Raises:
            ValueError: total size exceeds limit
        """
        total_size = sum(file_sizes)
        if total_size > self.MAX_TOTAL_SIZE:
            raise ValueError(
                f"Total file size ({total_size / 1024 / 1024:.2f}MB) exceeds limit ({self.MAX_TOTAL_SIZE / 1024 / 1024:.2f}MB)"
            )
        return True

    # ========== Session-Scoped Methods (New) ==========

    def save_uploaded_file_to_session(
        self,
        file_content: BinaryIO,
        filename: str,
        session_id: str,
        user_id: str | None = None,
    ) -> tuple[str, str]:
        """
        Save uploaded file to session directory

        Storage path: {UPLOAD_DIR}/{session_id}/{file_id}_{filename}

        Args:
            file_content: file content stream
            filename: original file name
            session_id: session ID
            user_id: user ID (optional, for logging purposes)

        Returns:
            (file_id, file_path) tuple

        Raises:
            FileTypeError: file type not supported
            ValueError: file size exceeds limit
        """
        # Sanitize file name
        safe_filename = self.sanitize_filename(filename)

        # Read file content
        content = file_content.read()
        file_size = len(content)

        # Validate file size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds limit ({self.MAX_FILE_SIZE / 1024 / 1024:.2f}MB)"
            )

        # Validate file type
        self.validate_file_type(safe_filename, content)

        # Generate file ID
        file_id = self.generate_file_id()

        # Create session directory: {UPLOAD_DIR}/{session_id}/
        session_dir = self.upload_dir / str(session_id)
        session_dir.mkdir(parents=True, exist_ok=True)

        # Build file path
        final_filename = f"{file_id}_{safe_filename}"
        file_path = session_dir / final_filename

        # Save file
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"File saved to session {session_id}: {file_path} (size: {file_size} bytes)")

        return file_id, str(file_path)

    def get_session_file_path(self, file_id: str, session_id: str) -> str | None:
        """
        Get file path from session directory

        Args:
            file_id: file ID
            session_id: session ID

        Returns:
            file path if found, otherwise None
        """
        session_dir = self.upload_dir / str(session_id)
        if not session_dir.exists():
            logger.warning(f"Session directory not found: {session_id}")
            return None

        for file_path in session_dir.glob(f"{file_id}_*"):
            if file_path.is_file():
                return str(file_path)

        logger.warning(f"File not found in session {session_id}: {file_id}")
        return None

    def delete_session_file(self, file_id: str, session_id: str) -> bool:
        """
        Delete file from session directory

        Args:
            file_id: file ID
            session_id: session ID

        Returns:
            whether the file was successfully deleted
        """
        file_path = self.get_session_file_path(file_id, session_id)
        if file_path is None:
            return False

        try:
            os.remove(file_path)
            logger.info(f"Deleted session file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    def delete_session_directory(self, session_id: str) -> int:
        """
        Delete entire session directory and all files

        Args:
            session_id: session ID

        Returns:
            Number of files deleted
        """
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
        """
        List all files in a specific session

        Args:
            session_id: session ID

        Returns:
            list of file metadata dicts
        """
        session_dir = self.upload_dir / str(session_id)
        if not session_dir.exists() or not session_dir.is_dir():
            logger.info(f"No files found for session {session_id}")
            return []

        files: list[dict[str, Any]] = []
        for file_path in sorted(session_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
            if not file_path.is_file():
                continue

            parts = file_path.name.split("_", 1)
            file_id = parts[0]
            original_filename = parts[1] if len(parts) > 1 else file_path.name

            stat = file_path.stat()

            files.append(
                {
                    "file_id": file_id,
                    "filename": original_filename,
                    "file_size": stat.st_size,
                    "file_path": str(file_path),
                    "upload_time": datetime.fromtimestamp(stat.st_mtime),
                    "session_id": str(session_id),
                }
            )

        return files


file_manager = FileManager()
