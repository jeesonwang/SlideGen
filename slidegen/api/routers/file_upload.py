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
from slidegen.utils.file import file_manager

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> Any:
    """
    Upload a single file

    Args:
        file: uploaded file
        current_user: current user

    Returns:
        FileUploadResponse: upload response
    """
    try:
        logger.info(f"User {current_user.id} uploading file: {file.filename}")

        # validate file exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="File name cannot be empty")

        # save file
        file_id, file_path = file_manager.save_uploaded_file(
            file_content=file.file,
            filename=file.filename,
            user_id=str(current_user.id),
        )

        # get file size
        file_size = len(file.file.read())
        file.file.seek(0)  # reset file pointer

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
    current_user: CurrentUser,
    files: list[UploadFile] = File(...),
) -> Any:
    """
    Upload multiple files

    Args:
        files: uploaded files list
        current_user: current user

    Returns:
        MultiFileUploadResponse: batch upload response
    """
    try:
        logger.info(f"User {current_user.id} uploading {len(files)} files")

        file_sizes = []
        for file in files:
            content = file.file.read()
            file_sizes.append(len(content))
            file.file.seek(0)  # reset file pointer

        try:
            file_manager.validate_total_size(file_sizes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # upload all files
        uploaded_files: list[FileUploadResponse] = []
        failed_files: list[dict[str, str]] = []

        for file in files:
            try:
                if not file.filename:
                    failed_files.append({"filename": "unknown", "error": "File name cannot be empty"})
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
                failed_files.append({"filename": file.filename or "", "error": str(e)})
            except Exception as e:
                logger.error(f"Unexpected error uploading {file.filename}: {e}")
                failed_files.append({"filename": file.filename or "", "error": "Upload failed"})

        success = len(failed_files) == 0
        message = (
            "All files uploaded successfully"
            if success
            else f"{len(uploaded_files)}/{len(files)} files uploaded successfully"
        )

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
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@router.get("/{file_id}", response_model=FileMetadata)
async def get_file_metadata(
    file_id: str,
    current_user: CurrentUser,
) -> Any:
    """
    Get file metadata

    Args:
        file_id: file ID
        current_user: current user

    Returns:
        FileMetadata: file metadata
    """
    try:
        # get file path
        file_path = file_manager.get_file_path(file_id, str(current_user.id))

        if file_path is None:
            raise HTTPException(status_code=404, detail="File not found")

        # read file information
        from datetime import datetime
        from pathlib import Path

        path = Path(file_path)
        stat = path.stat()

        # extract original file name from filename (format: {file_id}_{original_filename})
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
        raise HTTPException(status_code=500, detail=f"Failed to get file metadata: {str(e)}")


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: CurrentUser,
) -> dict[str, str]:
    """
    Delete file

    Args:
        file_id: file ID
        current_user: current user

    Returns:
        delete result
    """
    try:
        success = file_manager.delete_file(file_id, str(current_user.id))

        if not success:
            raise HTTPException(status_code=404, detail="File not found or delete failed")

        logger.info(f"File {file_id} deleted by user {current_user.id}")
        return {"message": "File deleted successfully", "file_id": file_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
