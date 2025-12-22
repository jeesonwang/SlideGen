import hashlib
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import BinaryIO

from loguru import logger

from slidegen.exception import FileTypeError


class FileManager:
    """管理上传文件的存储和检索"""

    # 允许的文件扩展名
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

    # 允许的MIME类型
    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/msword",  # .doc
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "application/vnd.ms-excel",  # .xls
        "text/html",  # .html
        "text/plain",  # .txt
        "text/markdown",  # .md
    }

    # 单个文件最大大小 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # 所有文件总大小限制 (50MB)
    MAX_TOTAL_SIZE = 50 * 1024 * 1024

    def __init__(self, upload_dir: str | Path | None = None):
        """
        初始化文件管理器

        Args:
            upload_dir: 上传文件存储目录,默认为 PROJECT_ROOT/outputs/uploads
        """
        if upload_dir is None:
            # 使用项目根目录下的 outputs/uploads
            project_root = Path(__file__).parent.parent.parent
            upload_dir = project_root / "outputs" / "uploads"

        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileManager initialized with upload directory: {self.upload_dir}")

    def generate_file_id(self) -> str:
        """
        生成唯一的文件ID

        Returns:
            UUID格式的文件ID
        """
        return str(uuid.uuid4())

    def validate_file_type(self, filename: str, content: bytes | None = None) -> bool:
        """
        验证文件类型是否允许

        Args:
            filename: 文件名
            content: 文件内容(可选,用于更精确的验证)

        Returns:
            是否允许该文件类型

        Raises:
            FileTypeError: 文件类型不被支持
        """
        # 检查文件扩展名
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise FileTypeError(f"不支持的文件类型: {ext}. 支持的类型: {', '.join(self.ALLOWED_EXTENSIONS)}")

        return True

    def sanitize_filename(self, filename: str) -> str:
        """
        清理文件名,防止路径遍历攻击

        Args:
            filename: 原始文件名

        Returns:
            安全的文件名
        """
        # 只保留文件名部分,去除路径
        filename = Path(filename).name

        # 移除危险字符
        unsafe_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
        for char in unsafe_chars:
            filename = filename.replace(char, "_")

        # 确保文件名不为空
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
        保存上传的文件

        Args:
            file_content: 文件内容流
            filename: 原始文件名
            user_id: 用户ID(可选)

        Returns:
            (file_id, file_path) 元组

        Raises:
            FileTypeError: 文件类型不被支持
            ValueError: 文件大小超过限制
        """
        # 清理文件名
        safe_filename = self.sanitize_filename(filename)

        # 读取文件内容
        content = file_content.read()
        file_size = len(content)

        # 验证文件大小
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"文件大小 ({file_size / 1024 / 1024:.2f}MB) 超过限制 ({self.MAX_FILE_SIZE / 1024 / 1024:.2f}MB)"
            )

        # 验证文件类型
        self.validate_file_type(safe_filename, content)

        # 生成文件ID
        file_id = self.generate_file_id()

        # 创建用户特定的目录(如果提供了user_id)
        if user_id:
            user_dir = self.upload_dir / str(user_id)
            user_dir.mkdir(parents=True, exist_ok=True)
            base_dir = user_dir
        else:
            base_dir = self.upload_dir

        # 构建文件路径: {file_id}_{original_filename}
        final_filename = f"{file_id}_{safe_filename}"
        file_path = base_dir / final_filename

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"File saved: {file_path} (size: {file_size} bytes)")

        return file_id, str(file_path)

    def get_file_path(self, file_id: str, user_id: str | None = None) -> str | None:
        """
        根据文件ID获取文件路径

        Args:
            file_id: 文件ID
            user_id: 用户ID(可选)

        Returns:
            文件路径,如果文件不存在则返回None
        """
        # 搜索目录
        search_dirs = []
        if user_id:
            search_dirs.append(self.upload_dir / str(user_id))
        search_dirs.append(self.upload_dir)

        # 在各个目录中搜索文件
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
        删除文件

        Args:
            file_id: 文件ID
            user_id: 用户ID(可选)

        Returns:
            是否成功删除
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

    def cleanup_old_files(self, days: int = 7) -> int:
        """
        清理过期的文件

        Args:
            days: 文件保留天数,超过这个天数的文件将被删除

        Returns:
            删除的文件数量
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for file_path in self.upload_dir.rglob("*"):
            if not file_path.is_file():
                continue

            try:
                # 获取文件修改时间
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
        计算文件的SHA256哈希值

        Args:
            file_path: 文件路径

        Returns:
            文件的SHA256哈希值
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def validate_total_size(self, file_sizes: list[int]) -> bool:
        """
        验证文件总大小是否超过限制

        Args:
            file_sizes: 文件大小列表(字节)

        Returns:
            是否在限制内

        Raises:
            ValueError: 总大小超过限制
        """
        total_size = sum(file_sizes)
        if total_size > self.MAX_TOTAL_SIZE:
            raise ValueError(
                f"文件总大小 ({total_size / 1024 / 1024:.2f}MB) 超过限制 ({self.MAX_TOTAL_SIZE / 1024 / 1024:.2f}MB)"
            )
        return True
