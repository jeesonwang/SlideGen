from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from loguru import logger

from slidegen.api.deps import CurrentUser
from slidegen.exceptions import FileTypeError
from slidegen.schemas.file_upload import (
    FileMetadata,
    FileUploadResponse,
    MultiFileUploadResponse,
)
from slidegen.utils.file import FileManager

router = APIRouter(tags=["文件管理"])

# 初始化文件管理器
file_manager = FileManager()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: CurrentUser = ...,
) -> Any:
    """
    上传单个文件

    Args:
        file: 上传的文件
        current_user: 当前用户

    Returns:
        FileUploadResponse: 上传响应
    """
    try:
        logger.info(f"User {current_user.id} uploading file: {file.filename}")

        # 验证文件存在
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 保存文件
        file_id, file_path = file_manager.save_uploaded_file(
            file_content=file.file,
            filename=file.filename,
            user_id=str(current_user.id),
        )

        # 获取文件大小
        file_size = len(file.file.read())
        file.file.seek(0)  # 重置文件指针

        response = FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type,
        )

        logger.info(f"File uploaded successfully: {file_id}")
        return response

    except FileTypeError as e:
        logger.warning(f"File type error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.warning(f"File size error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/upload-multiple", response_model=MultiFileUploadResponse)
async def upload_multiple_files(
    files: list[UploadFile] = File(...),
    current_user: CurrentUser = ...,
) -> Any:
    """
    上传多个文件

    Args:
        files: 上传的文件列表
        current_user: 当前用户

    Returns:
        MultiFileUploadResponse: 批量上传响应
    """
    try:
        logger.info(f"User {current_user.id} uploading {len(files)} files")

        # 验证文件总大小
        file_sizes = []
        for file in files:
            content = file.file.read()
            file_sizes.append(len(content))
            file.file.seek(0)  # 重置文件指针

        try:
            file_manager.validate_total_size(file_sizes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 上传所有文件
        uploaded_files: list[FileUploadResponse] = []
        failed_files: list[dict[str, str]] = []

        for file in files:
            try:
                if not file.filename:
                    failed_files.append({"filename": "unknown", "error": "文件名为空"})
                    continue

                file_id, file_path = file_manager.save_uploaded_file(
                    file_content=file.file,
                    filename=file.filename,
                    user_id=str(current_user.id),
                )

                file_size = file_sizes[files.index(file)]

                uploaded_files.append(
                    FileUploadResponse(
                        file_id=file_id,
                        filename=file.filename,
                        file_size=file_size,
                        content_type=file.content_type,
                    )
                )

            except (FileTypeError, ValueError) as e:
                logger.warning(f"Failed to upload {file.filename}: {e}")
                failed_files.append({"filename": file.filename, "error": str(e)})
            except Exception as e:
                logger.error(f"Unexpected error uploading {file.filename}: {e}")
                failed_files.append({"filename": file.filename, "error": "上传失败"})

        success = len(failed_files) == 0
        message = "所有文件上传成功" if success else f"{len(uploaded_files)}/{len(files)} 文件上传成功"

        logger.info(f"Batch upload completed: {len(uploaded_files)} succeeded, {len(failed_files)} failed")

        return MultiFileUploadResponse(
            success=success,
            files=uploaded_files,
            failed_files=failed_files,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to upload files: {e}")
        raise HTTPException(status_code=500, detail=f"批量上传失败: {str(e)}")


@router.get("/{file_id}", response_model=FileMetadata)
async def get_file_metadata(
    file_id: str,
    current_user: CurrentUser,
) -> Any:
    """
    获取文件元数据

    Args:
        file_id: 文件ID
        current_user: 当前用户

    Returns:
        FileMetadata: 文件元数据
    """
    try:
        # 获取文件路径
        file_path = file_manager.get_file_path(file_id, str(current_user.id))

        if file_path is None:
            raise HTTPException(status_code=404, detail="文件未找到")

        # 读取文件信息
        from datetime import datetime
        from pathlib import Path

        path = Path(file_path)
        stat = path.stat()

        # 从文件名提取原始文件名 (格式: {file_id}_{original_filename})
        filename_parts = path.name.split("_", 1)
        original_filename = filename_parts[1] if len(filename_parts) > 1 else path.name

        metadata = FileMetadata(
            file_id=file_id,
            filename=original_filename,
            file_size=stat.st_size,
            file_path=file_path,
            upload_time=datetime.fromtimestamp(stat.st_mtime),
            user_id=str(current_user.id),
        )

        return metadata

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get file metadata: {e}")
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: CurrentUser,
) -> dict[str, str]:
    """
    删除文件

    Args:
        file_id: 文件ID
        current_user: 当前用户

    Returns:
        删除结果
    """
    try:
        success = file_manager.delete_file(file_id, str(current_user.id))

        if not success:
            raise HTTPException(status_code=404, detail="文件未找到或删除失败")

        logger.info(f"File {file_id} deleted by user {current_user.id}")
        return {"message": "文件删除成功", "file_id": file_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")
