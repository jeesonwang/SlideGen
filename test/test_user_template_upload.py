import uuid

from slidegen.models.presentation_template import PresentationTemplateModel
from slidegen.schemas.template import (
    Template,
    TemplateProfileResponse,
    TemplateRoleAssignmentResponse,
    TemplateSource,
    UserTemplateUploadResponse,
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
