import uuid
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import UploadFile
from pptx import Presentation
from pptx.util import Inches

from slidegen.models.presentation_template import PresentationTemplateModel
from slidegen.schemas.template import (
    Template,
    TemplateProfileResponse,
    TemplateRoleAssignmentResponse,
    TemplateSource,
    UserTemplateUploadResponse,
)
from slidegen.services.presentation.user_templates import (
    USER_TEMPLATE_KEY_PREFIX,
    UploadedTemplateService,
    UserTemplateStorage,
    parse_user_template_key,
    template_key_for_id,
)


def test_user_template_model_defaults_to_review_required() -> None:
    user_id = uuid.uuid4()
    template = PresentationTemplateModel(
        user_id=user_id,
        name="Board Template",
        original_filename="board.pptx",
        file_path="/tmp/board.pptx",
        file_size=1024,
        content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        file_hash="a" * 64,
        template_key="user_1234567890abcdef1234567890abcdef",
        slide_count=5,
        role_profile={"assignments": []},
        warnings=[],
    )

    assert template.user_id == user_id
    assert template.status == "review_required"
    assert template.is_deleted is False


def test_template_schema_exposes_profile_for_uploaded_templates() -> None:
    assignment = TemplateRoleAssignmentResponse(
        role="cover",
        slide_index=0,
        confidence=0.95,
        reason="first slide",
    )
    profile = TemplateProfileResponse(
        slide_count=5,
        status="ready",
        assignments=[assignment],
        warnings=[],
        missing_roles=[],
    )

    template = Template(
        id="user_1234567890abcdef1234567890abcdef",
        name="Board Template",
        thumbnail=None,
        source=TemplateSource.USER,
        profile_status="ready",
        role_profile=profile,
    )

    assert template.source is TemplateSource.USER
    assert template.role_profile is profile


def test_user_template_upload_response_contains_template_key() -> None:
    template_id = uuid.uuid4()
    response = UserTemplateUploadResponse(
        id=template_id,
        template_key=f"user_{template_id.hex}",
        name="Board Template",
        original_filename="board.pptx",
        file_size=1024,
        profile=TemplateProfileResponse(
            slide_count=5,
            status="ready",
            assignments=[],
            warnings=[],
            missing_roles=[],
        ),
        message="Template uploaded successfully",
    )

    assert response.template_key == f"user_{template_id.hex}"


def _pptx_upload_bytes() -> bytes:
    prs = Presentation()
    for lines in (
        ["Quarterly Business Review", "2026 Strategy Update"],
        ["Agenda", "1. Market", "2. Product", "3. Finance"],
        ["Chapter 1", "Market"],
        ["Market", "Revenue grew 18 percent.", "Enterprise demand increased.", "Retention is stable."],
        ["Thank You", "Questions"],
    ):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        textbox = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(8.0), Inches(4.5))
        frame = textbox.text_frame
        frame.text = lines[0]
        for line in lines[1:]:
            paragraph = frame.add_paragraph()
            paragraph.text = line

    stream = BytesIO()
    prs.save(stream)
    return stream.getvalue()


def _upload_file(filename: str, content: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(content),
        headers={"content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
    )


class _FakeDbSession:
    def __init__(self) -> None:
        self.added = None
        self.add = Mock(side_effect=self._add)
        self.commit = AsyncMock()
        self.refresh = AsyncMock()

    def _add(self, obj) -> None:
        self.added = obj


def test_template_key_round_trips_uuid() -> None:
    template_id = uuid.uuid4()

    key = template_key_for_id(template_id)

    assert key == f"{USER_TEMPLATE_KEY_PREFIX}{template_id.hex}"
    assert parse_user_template_key(key) == template_id
    assert parse_user_template_key("general") is None


def test_storage_rejects_non_pptx_extension(tmp_path: Path) -> None:
    storage = UserTemplateStorage(tmp_path, max_file_size=10_000_000)

    with pytest.raises(ValueError, match="Only .pptx template files are supported"):
        storage.validate_upload("template.pdf", b"fake")


@pytest.mark.anyio
async def test_upload_service_saves_pptx_profiles_and_persists_model(tmp_path: Path) -> None:
    user_id = uuid.uuid4()
    db_session = _FakeDbSession()
    service = UploadedTemplateService(
        storage=UserTemplateStorage(tmp_path, max_file_size=10_000_000),
    )
    upload = _upload_file("board template.pptx", _pptx_upload_bytes())

    response = await service.upload_template(
        db_session=db_session,
        user_id=user_id,
        upload_file=upload,
        display_name="Board Template",
    )

    assert response.template_key.startswith(USER_TEMPLATE_KEY_PREFIX)
    assert response.name == "Board Template"
    assert response.profile.status == "ready"
    assert db_session.added is not None
    assert db_session.added.user_id == user_id
    assert db_session.added.template_key == response.template_key
    assert Path(db_session.added.file_path).exists()
    db_session.add.assert_called_once()
    db_session.commit.assert_awaited_once()
    db_session.refresh.assert_awaited_once()
