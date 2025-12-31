import uuid
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from loguru import logger
from sqlmodel import select

from slidegen.api.deps import CurrentUser, SessionDep
from slidegen.exceptions import FileTypeError
from slidegen.models.file_metadata import FileMetadataModel, FileMetadataPublic, FileMetadatasPublic
from slidegen.models.session import SessionModel, SessionStatus
from slidegen.schemas.file_upload import FileUploadResponse, MultiFileUploadResponse
from slidegen.utils.file import file_manager

router = APIRouter()


async def validate_session_for_upload(
    db_session: SessionDep, session_id: uuid.UUID, user_id: uuid.UUID
) -> SessionModel:
    """
    Validate session exists, belongs to user, and is in ACTIVE status

    Args:
        db_session: database session
        session_id: session ID
        user_id: user ID

    Returns:
        SessionModel if valid

    Raises:
        HTTPException: if validation fails
    """
    session = await db_session.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Cannot upload files to session with status: {session.status}")
    return session


@router.post("/{session_id}/files/upload", response_model=FileUploadResponse)
async def upload_file_to_session(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db_session: SessionDep,
    file: UploadFile = File(...),
) -> Any:
    """
    Upload file to a specific session

    - Validate session exists and belongs to user
    - Validate session is ACTIVE
    - Save to {UPLOAD_DIR}/{session_id}/{file_id}_{filename}
    - Create FileMetadataModel record
    """
    try:
        logger.info(f"User {current_user.id} uploading file to session {session_id}: {file.filename}")

        # Validate session
        await validate_session_for_upload(db_session, session_id, current_user.id)

        # Validate file exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="File name cannot be empty")

        # Save file to session directory
        file_id, file_path = file_manager.save_uploaded_file_to_session(
            file_content=file.file, filename=file.filename, session_id=str(session_id), user_id=str(current_user.id)
        )

        # Calculate file hash
        file_hash = file_manager.get_file_hash(file_path)

        # Get file size
        content = file.file.read()
        file_size = len(content)
        file.file.seek(0)  # reset file pointer

        # Create database record
        file_metadata = FileMetadataModel(
            id=uuid.UUID(file_id),
            session_id=session_id,
            user_id=current_user.id,
            filename=file.filename,
            file_size=file_size,
            file_path=file_path,
            content_type=file.content_type,
            file_hash=file_hash,
            parsed=False,
        )

        db_session.add(file_metadata)
        await db_session.commit()
        await db_session.refresh(file_metadata)

        logger.info(f"File uploaded successfully to session {session_id}: {file_id}")

        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_size=file_size,
            content_type=file.content_type,
        )

    except FileTypeError as e:
        logger.warning(f"File type error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.warning(f"File size error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.post("/{session_id}/files/upload-multiple", response_model=MultiFileUploadResponse)
async def upload_multiple_files_to_session(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db_session: SessionDep,
    files: list[UploadFile] = File(...),
) -> Any:
    """
    Batch upload files to session

    - Validates each file individually
    - Continues on errors (partial success allowed)
    - Returns list of successful uploads and failed uploads
    """
    try:
        logger.info(f"User {current_user.id} uploading {len(files)} files to session {session_id}")

        # Validate session
        await validate_session_for_upload(db_session, session_id, current_user.id)

        # Validate total size
        file_sizes = []
        for file in files:
            content = file.file.read()
            file_sizes.append(len(content))
            file.file.seek(0)  # reset file pointer

        try:
            file_manager.validate_total_size(file_sizes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Upload all files
        uploaded_files: list[FileUploadResponse] = []
        failed_files: list[dict[str, str]] = []

        for idx, file in enumerate(files):
            try:
                if not file.filename:
                    failed_files.append({"filename": "unknown", "error": "File name cannot be empty"})
                    continue

                # Save file
                file_id, file_path = file_manager.save_uploaded_file_to_session(
                    file_content=file.file,
                    filename=file.filename,
                    session_id=str(session_id),
                    user_id=str(current_user.id),
                )

                # Calculate file hash
                file_hash = file_manager.get_file_hash(file_path)

                # Get file size
                file_size = file_sizes[idx]

                # Create database record
                file_metadata = FileMetadataModel(
                    id=uuid.UUID(file_id),
                    session_id=session_id,
                    user_id=current_user.id,
                    filename=file.filename,
                    file_size=file_size,
                    file_path=file_path,
                    content_type=file.content_type,
                    file_hash=file_hash,
                    parsed=False,
                )

                db_session.add(file_metadata)
                await db_session.flush()  # Flush to database but don't commit yet

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

        # Commit all successful uploads
        await db_session.commit()

        success = len(failed_files) == 0
        message = (
            "All files uploaded successfully"
            if success
            else f"{len(uploaded_files)}/{len(files)} files uploaded successfully"
        )

        logger.info(
            f"Batch upload to session {session_id}: {len(uploaded_files)} succeeded, {len(failed_files)} failed"
        )

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


@router.get("/{session_id}/files", response_model=FileMetadatasPublic)
async def list_session_files(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db_session: SessionDep,
) -> Any:
    """
    List all files in a session

    - Query FileMetadataModel by session_id
    - Security: Verify session ownership
    """
    try:
        # Validate session ownership
        session = await db_session.get(SessionModel, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Query files
        statement = select(FileMetadataModel).where(FileMetadataModel.session_id == session_id)
        result = await db_session.execute(statement)
        files = result.scalars().all()

        # Convert to public schema
        file_publics = [
            FileMetadataPublic(
                id=f.id,
                session_id=f.session_id,
                user_id=f.user_id,
                filename=f.filename,
                file_size=f.file_size,
                file_path=f.file_path,
                content_type=f.content_type,
                file_hash=f.file_hash,
                parsed=f.parsed,
                parse_error=f.parse_error,
                create_time=f.create_time,
                update_time=f.update_time,
            )
            for f in files
        ]

        return FileMetadatasPublic(data=file_publics, count=len(file_publics))

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list session files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@router.get("/{session_id}/files/{file_id}", response_model=FileMetadataPublic)
async def get_session_file(
    session_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: CurrentUser,
    db_session: SessionDep,
) -> Any:
    """
    Get file metadata from session

    - Security: Verify session ownership
    - Verify file belongs to session
    """
    try:
        # Validate session ownership
        session = await db_session.get(SessionModel, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get file metadata
        file_metadata = await db_session.get(FileMetadataModel, file_id)
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        if file_metadata.session_id != session_id:
            raise HTTPException(status_code=400, detail="File does not belong to this session")

        return FileMetadataPublic(
            id=file_metadata.id,
            session_id=file_metadata.session_id,
            user_id=file_metadata.user_id,
            filename=file_metadata.filename,
            file_size=file_metadata.file_size,
            file_path=file_metadata.file_path,
            content_type=file_metadata.content_type,
            file_hash=file_metadata.file_hash,
            parsed=file_metadata.parsed,
            parse_error=file_metadata.parse_error,
            create_time=file_metadata.create_time,
            update_time=file_metadata.update_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get file metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get file: {str(e)}")


@router.delete("/{session_id}/files/{file_id}")
async def delete_session_file(
    session_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: CurrentUser,
    db_session: SessionDep,
) -> dict[str, str]:
    """
    Delete file from session

    - Remove from filesystem
    - Delete FileMetadataModel record
    - Security: Verify session ownership and file belongs to session
    """
    try:
        # Validate session ownership
        session = await db_session.get(SessionModel, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get file metadata
        file_metadata = await db_session.get(FileMetadataModel, file_id)
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        if file_metadata.session_id != session_id:
            raise HTTPException(status_code=400, detail="File does not belong to this session")

        # Delete from filesystem
        success = file_manager.delete_session_file(str(file_id), str(session_id))
        if not success:
            logger.warning(f"File not found on filesystem: {file_id}")

        # Delete from database
        await db_session.delete(file_metadata)
        await db_session.commit()

        logger.info(f"File {file_id} deleted from session {session_id}")

        return {"message": "File deleted successfully", "file_id": str(file_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
