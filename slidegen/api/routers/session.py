import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from sqlalchemy import func
from sqlmodel import select

from slidegen.api.deps import CurrentUser, SessionDep
from slidegen.core.config import settings
from slidegen.models.chat_message import ChatMessageModel
from slidegen.models.file_metadata import FileMetadataModel
from slidegen.models.session import (
    SessionCreate,
    SessionModel,
    SessionPublic,
    SessionsPublic,
    SessionStatus,
    SessionUpdate,
)
from slidegen.utils.file import file_manager

router = APIRouter()


async def validate_session_limit(db_session: SessionDep, user_id: uuid.UUID) -> bool:
    """
    Check if user has reached session limit

    Args:
        db_session: database session
        user_id: user ID

    Returns:
        True if within limit

    Raises:
        HTTPException: if session limit reached
    """
    count_statement = (
        select(func.count())
        .select_from(SessionModel)
        .where(
            SessionModel.user_id == user_id,
            SessionModel.status.in_([SessionStatus.ACTIVE, SessionStatus.COMPLETED]),  # type: ignore
        )
    )
    active_count = (await db_session.execute(count_statement)).scalar_one()

    if active_count >= settings.MAX_ACTIVE_SESSIONS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_ACTIVE_SESSIONS_PER_USER} active sessions reached. Please archive or delete old sessions.",
        )
    return True


async def validate_session_ownership(db_session: SessionDep, session_id: uuid.UUID, user_id: uuid.UUID) -> SessionModel:
    """
    Ensure user owns the session

    Args:
        db_session: database session
        session_id: session ID
        user_id: user ID

    Returns:
        SessionModel if owned by user

    Raises:
        HTTPException: if session not found or access denied
    """
    session = await db_session.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return session


@router.post("/", response_model=SessionPublic, status_code=201)
async def create_session(
    *,
    db_session: SessionDep,
    current_user: CurrentUser,
    session_in: SessionCreate,
) -> Any:
    """
    Create a new session for PPT generation

    - Validates session limit per user
    - Auto-generates session ID
    - Sets status to ACTIVE by default
    """
    try:
        # Validate session limit
        await validate_session_limit(db_session, current_user.id)

        # Create session
        session = SessionModel(
            user_id=current_user.id,
            title=session_in.title,
            status=session_in.status,
            topic=session_in.topic,
            extra_data=session_in.extra_data,
        )

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        logger.info(f"Session created: {session.id} for user {current_user.id}")

        # Return with counts
        return SessionPublic(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            status=session.status,
            topic=session.topic,
            extra_data=session.extra_data,
            file_count=0,
            message_count=0,
            create_time=session.create_time,
            update_time=session.update_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/", response_model=SessionsPublic)
async def list_sessions(
    db_session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    status: SessionStatus | None = None,
    search: str | None = Query(None, description="Search in title/topic"),
) -> Any:
    """
    List all sessions for current user

    - Supports pagination (skip/limit)
    - Filter by status
    - Full-text search on title/topic
    - Ordered by create_time DESC
    """
    try:
        # Build query
        statement = select(SessionModel).where(SessionModel.user_id == current_user.id)

        # Filter by status
        if status:
            statement = statement.where(SessionModel.status == status)

        # Search in title/topic
        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                (SessionModel.title.ilike(search_pattern)) | (SessionModel.topic.ilike(search_pattern))  # type: ignore
            )

        # Get total count
        count_statement = select(func.count()).select_from(statement.subquery())
        total = (await db_session.execute(count_statement)).scalar_one()

        # Order and paginate
        statement = statement.order_by(SessionModel.create_time.desc()).offset(skip).limit(limit)  # type: ignore

        # Execute query
        result = await db_session.execute(statement)
        sessions = result.scalars().all()

        # Get file and message counts for each session
        session_publics = []
        for session in sessions:
            # Count files
            file_count_stmt = (
                select(func.count()).select_from(FileMetadataModel).where(FileMetadataModel.session_id == session.id)
            )
            file_count = (await db_session.execute(file_count_stmt)).scalar_one()

            # Count messages
            msg_count_stmt = (
                select(func.count()).select_from(ChatMessageModel).where(ChatMessageModel.session_id == session.id)
            )
            message_count = (await db_session.execute(msg_count_stmt)).scalar_one()

            session_publics.append(
                SessionPublic(
                    id=session.id,
                    user_id=session.user_id,
                    title=session.title,
                    status=session.status,
                    topic=session.topic,
                    extra_data=session.extra_data,
                    file_count=file_count,
                    message_count=message_count,
                    create_time=session.create_time,
                    update_time=session.update_time,
                )
            )

        return SessionsPublic(data=session_publics, count=total)

    except Exception as e:
        logger.exception(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/{session_id}", response_model=SessionPublic)
async def get_session(
    db_session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
) -> Any:
    """
    Get session details with file_count and message_count

    - Security: Only owner can access
    """
    try:
        # Validate ownership
        session = await validate_session_ownership(db_session, session_id, current_user.id)

        # Count files
        file_count_stmt = (
            select(func.count()).select_from(FileMetadataModel).where(FileMetadataModel.session_id == session_id)
        )
        file_count = (await db_session.execute(file_count_stmt)).scalar_one()

        # Count messages
        msg_count_stmt = (
            select(func.count()).select_from(ChatMessageModel).where(ChatMessageModel.session_id == session_id)
        )
        message_count = (await db_session.execute(msg_count_stmt)).scalar_one()

        return SessionPublic(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            status=session.status,
            topic=session.topic,
            extra_data=session.extra_data,
            file_count=file_count,
            message_count=message_count,
            create_time=session.create_time,
            update_time=session.update_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.patch("/{session_id}", response_model=SessionPublic)
async def update_session(
    *,
    db_session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
    session_in: SessionUpdate,
) -> Any:
    """
    Update session (title, status, metadata)

    - Security: Only owner can update
    - Cannot change user_id
    """
    try:
        # Validate ownership
        session = await validate_session_ownership(db_session, session_id, current_user.id)

        # Update fields
        if session_in.title is not None:
            session.title = session_in.title
        if session_in.status is not None:
            session.status = session_in.status
        if session_in.topic is not None:
            session.topic = session_in.topic
        if session_in.extra_data is not None:
            session.extra_data = session_in.extra_data

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        logger.info(f"Session updated: {session_id}")

        # Get counts
        file_count_stmt = (
            select(func.count()).select_from(FileMetadataModel).where(FileMetadataModel.session_id == session_id)
        )
        file_count = (await db_session.execute(file_count_stmt)).scalar_one()

        msg_count_stmt = (
            select(func.count()).select_from(ChatMessageModel).where(ChatMessageModel.session_id == session_id)
        )
        message_count = (await db_session.execute(msg_count_stmt)).scalar_one()

        return SessionPublic(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            status=session.status,
            topic=session.topic,
            extra_data=session.extra_data,
            file_count=file_count,
            message_count=message_count,
            create_time=session.create_time,
            update_time=session.update_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(
    db_session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
    permanent: bool = Query(False, description="Permanent delete vs soft delete"),
) -> dict[str, str]:
    """
    Delete session and all associated data

    - Soft delete by default (status=DELETED)
    - permanent=True: Hard delete from DB + filesystem cleanup
    - Cascade deletes: files, messages, knowledge base
    """
    try:
        # Validate ownership
        session = await validate_session_ownership(db_session, session_id, current_user.id)

        if permanent:
            # Hard delete: delete files from filesystem first
            deleted_file_count = file_manager.delete_session_directory(str(session_id))
            logger.info(f"Deleted {deleted_file_count} files from session {session_id}")

            # Delete from database (cascade will handle file_metadata and chat_messages)
            await db_session.delete(session)
            await db_session.commit()

            logger.info(f"Permanently deleted session: {session_id}")
            return {"message": "Session permanently deleted", "session_id": str(session_id)}

        else:
            # Soft delete: just update status
            session.status = SessionStatus.DELETED
            db_session.add(session)
            await db_session.commit()

            logger.info(f"Soft deleted session: {session_id}")
            return {"message": "Session archived (soft delete)", "session_id": str(session_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.post("/{session_id}/archive", response_model=SessionPublic)
async def archive_session(
    db_session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
) -> Any:
    """Archive session (set status to ARCHIVED)"""
    try:
        # Validate ownership
        session = await validate_session_ownership(db_session, session_id, current_user.id)

        # Archive
        session.status = SessionStatus.ARCHIVED
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        logger.info(f"Session archived: {session_id}")

        # Get counts
        file_count_stmt = (
            select(func.count()).select_from(FileMetadataModel).where(FileMetadataModel.session_id == session_id)
        )
        file_count = (await db_session.execute(file_count_stmt)).scalar_one()

        msg_count_stmt = (
            select(func.count()).select_from(ChatMessageModel).where(ChatMessageModel.session_id == session_id)
        )
        message_count = (await db_session.execute(msg_count_stmt)).scalar_one()

        return SessionPublic(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            status=session.status,
            topic=session.topic,
            extra_data=session.extra_data,
            file_count=file_count,
            message_count=message_count,
            create_time=session.create_time,
            update_time=session.update_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to archive session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to archive session: {str(e)}")
