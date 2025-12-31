import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from loguru import logger
from sqlmodel import select

from slidegen.api.deps import CurrentUser, SessionDep
from slidegen.models.chat_message import ChatMessageCreate, ChatMessageModel, ChatMessagePublic, ChatMessagesPublic
from slidegen.models.session import SessionModel

router = APIRouter()


@router.post("/{session_id}/messages", response_model=ChatMessagePublic, status_code=201)
async def add_message(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db_session: SessionDep,
    message_in: ChatMessageCreate,
) -> Any:
    """
    Add a chat message to session

    - Validate session exists and belongs to user
    - Store message with timestamp
    """
    try:
        # Validate session ownership
        session = await db_session.get(SessionModel, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Verify message session_id matches URL param
        if message_in.session_id != session_id:
            raise HTTPException(status_code=400, detail="Session ID mismatch")

        # Create message
        message = ChatMessageModel(
            session_id=session_id,
            user_id=current_user.id,
            role=message_in.role,
            content=message_in.content,
            extra_data=message_in.extra_data,
        )

        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)

        logger.info(f"Message added to session {session_id}: {message.id}")

        return ChatMessagePublic(
            id=message.id,
            session_id=message.session_id,
            user_id=message.user_id,
            role=message.role,
            content=message.content,
            extra_data=message.extra_data,
            create_time=message.create_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to add message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.get("/{session_id}/messages", response_model=ChatMessagesPublic)
async def list_messages(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    db_session: SessionDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get chat history for a session

    - Ordered by create_time ASC (chronological)
    - Pagination support
    """
    try:
        # Validate session ownership
        session = await db_session.get(SessionModel, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Query messages
        statement = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.create_time.asc())  # type: ignore
            .offset(skip)
            .limit(limit)
        )

        result = await db_session.execute(statement)
        messages = result.scalars().all()

        # Get total count
        from sqlalchemy import func

        count_statement = (
            select(func.count()).select_from(ChatMessageModel).where(ChatMessageModel.session_id == session_id)
        )
        total = (await db_session.execute(count_statement)).scalar_one()

        # Convert to public schema
        message_publics = [
            ChatMessagePublic(
                id=msg.id,
                session_id=msg.session_id,
                user_id=msg.user_id,
                role=msg.role,
                content=msg.content,
                extra_data=msg.extra_data,
                create_time=msg.create_time,
            )
            for msg in messages
        ]

        return ChatMessagesPublic(data=message_publics, count=total)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list messages: {str(e)}")


@router.get("/{session_id}/messages/{message_id}", response_model=ChatMessagePublic)
async def get_message(
    session_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: CurrentUser,
    db_session: SessionDep,
) -> Any:
    """
    Get a specific message

    - Security: Verify session ownership and message belongs to session
    """
    try:
        # Validate session ownership
        session = await db_session.get(SessionModel, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get message
        message = await db_session.get(ChatMessageModel, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        if message.session_id != session_id:
            raise HTTPException(status_code=400, detail="Message does not belong to this session")

        return ChatMessagePublic(
            id=message.id,
            session_id=message.session_id,
            user_id=message.user_id,
            role=message.role,
            content=message.content,
            extra_data=message.extra_data,
            create_time=message.create_time,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get message: {str(e)}")


@router.delete("/{session_id}/messages/{message_id}")
async def delete_message(
    session_id: uuid.UUID,
    message_id: uuid.UUID,
    current_user: CurrentUser,
    db_session: SessionDep,
) -> dict[str, str]:
    """
    Delete a specific message (for edit/correction use cases)

    - Security: Verify session ownership and message belongs to session
    """
    try:
        # Validate session ownership
        session = await db_session.get(SessionModel, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get message
        message = await db_session.get(ChatMessageModel, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        if message.session_id != session_id:
            raise HTTPException(status_code=400, detail="Message does not belong to this session")

        # Delete message
        await db_session.delete(message)
        await db_session.commit()

        logger.info(f"Message {message_id} deleted from session {session_id}")

        return {"message": "Message deleted successfully", "message_id": str(message_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")
