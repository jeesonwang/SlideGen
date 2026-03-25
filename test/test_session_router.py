import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from slidegen.api.routers.session import delete_session, list_sessions
from slidegen.models.session import SessionStatus


class _ScalarResult:
    def __init__(self, value: int) -> None:
        self.value = value

    def scalar_one(self) -> int:
        return self.value


class _RowsResult:
    def __init__(self, rows: list[tuple[SimpleNamespace, int, int]]) -> None:
        self.rows = rows

    def all(self) -> list[tuple[SimpleNamespace, int, int]]:
        return self.rows


async def test_delete_session_permanently_removes_session_by_default() -> None:
    session_id = uuid.uuid4()
    current_user = SimpleNamespace(id=uuid.uuid4())
    session = SimpleNamespace(id=session_id, status=SessionStatus.ACTIVE)
    db_session = SimpleNamespace(
        delete=AsyncMock(),
        commit=AsyncMock(),
        add=AsyncMock(),
    )

    with (
        patch(
            "slidegen.api.routers.session.validate_session_ownership",
            new=AsyncMock(return_value=session),
        ) as validate_mock,
        patch(
            "slidegen.api.routers.session.file_manager.delete_session_directory",
            return_value=4,
        ) as delete_dir_mock,
    ):
        result = await delete_session(
            db_session=db_session,
            current_user=current_user,
            session_id=session_id,
        )

    validate_mock.assert_awaited_once_with(db_session, session_id, current_user.id)
    delete_dir_mock.assert_called_once_with(str(session_id))
    db_session.delete.assert_awaited_once_with(session)
    db_session.commit.assert_awaited_once()
    db_session.add.assert_not_called()
    assert session.status == SessionStatus.ACTIVE
    assert result == {
        "message": "Session permanently deleted",
        "session_id": str(session_id),
    }


async def test_list_sessions_excludes_deleted_status_by_default() -> None:
    current_user = SimpleNamespace(id=uuid.uuid4())
    statements: list[tuple[str, dict[str, object]]] = []
    active_session = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title="Active session",
        status=SessionStatus.ACTIVE,
        topic=None,
        extra_data=None,
        create_time="2026-03-01T10:00:00Z",
        update_time="2026-03-01T10:00:00Z",
    )
    completed_session = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title="Completed session",
        status=SessionStatus.COMPLETED,
        topic=None,
        extra_data=None,
        create_time="2026-03-02T10:00:00Z",
        update_time="2026-03-02T10:00:00Z",
    )

    async def execute(statement):
        compiled = statement.compile()
        statements.append((str(statement), compiled.params))
        if len(statements) == 1:
            return _ScalarResult(2)
        return _RowsResult(
            [
                (active_session, 0, 0),
                (completed_session, 1, 3),
            ]
        )

    db_session = SimpleNamespace(execute=AsyncMock(side_effect=execute))

    result = await list_sessions(
        db_session=db_session,
        current_user=current_user,
        skip=0,
        limit=100,
        status=None,
        search=None,
    )

    assert result.count == 2
    assert [session.status for session in result.data] == [
        SessionStatus.ACTIVE,
        SessionStatus.COMPLETED,
    ]
    assert len(statements) == 2
    assert all("sessions.status !=" in sql for sql, _ in statements)
    assert all(
        SessionStatus.DELETED in params.values()
        for _, params in statements
    )
