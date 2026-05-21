from __future__ import annotations

import hashlib
import shutil
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from pptx import Presentation
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from slidegen.core.config import settings
from slidegen.models.presentation_template import PresentationTemplateModel
from slidegen.schemas.template import (
    Template,
    TemplateProfileResponse,
    TemplateRoleAssignmentResponse,
    TemplateSource,
    UserTemplateDeleteResponse,
    UserTemplateUploadResponse,
)
from slidegen.services.presentation.template_profile import TemplateProfile, profile_presentation_template

USER_TEMPLATE_KEY_PREFIX = "user_"
PPTX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def template_key_for_id(template_id: uuid.UUID) -> str:
    return f"{USER_TEMPLATE_KEY_PREFIX}{template_id.hex}"


def parse_user_template_key(template_key: str) -> uuid.UUID | None:
    if not template_key.startswith(USER_TEMPLATE_KEY_PREFIX):
        return None
    value = template_key.removeprefix(USER_TEMPLATE_KEY_PREFIX)
    try:
        return uuid.UUID(hex=value)
    except ValueError:
        return None


def _profile_response(profile: TemplateProfile) -> TemplateProfileResponse:
    return TemplateProfileResponse(
        slide_count=profile.slide_count,
        status=profile.status,
        assignments=[TemplateRoleAssignmentResponse(**assignment.to_dict()) for assignment in profile.assignments],
        warnings=profile.warnings,
        missing_roles=profile.missing_roles,
    )


def _profile_dict(profile: TemplateProfile) -> dict[str, Any]:
    return profile.to_dict()


class UserTemplateStorage:
    def __init__(
        self,
        base_dir: Path | None = None,
        max_file_size: int | None = None,
    ) -> None:
        self.base_dir = base_dir or settings.USER_TEMPLATES_DIR
        self.max_file_size = max_file_size or settings.MAX_TEMPLATE_FILE_SIZE
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_upload(self, filename: str, content: bytes) -> None:
        if not filename:
            raise ValueError("File name cannot be empty")
        if Path(filename).suffix.lower() != ".pptx":
            raise ValueError("Only .pptx template files are supported")
        if not content:
            raise ValueError("Template file cannot be empty")
        if len(content) > self.max_file_size:
            max_mb = self.max_file_size / 1024 / 1024
            raise ValueError(f"Template file exceeds {max_mb:.0f}MB limit")

    def template_dir(self, user_id: uuid.UUID, template_id: uuid.UUID) -> Path:
        return self.base_dir / str(user_id) / str(template_id)

    def template_path(self, user_id: uuid.UUID, template_id: uuid.UUID) -> Path:
        return self.template_dir(user_id, template_id) / "template.pptx"

    def save(
        self, user_id: uuid.UUID, template_id: uuid.UUID, filename: str, content: bytes
    ) -> tuple[Path, Presentation]:
        self.validate_upload(filename, content)
        try:
            presentation = Presentation(BytesIO(content))
        except Exception as exc:
            raise ValueError("Uploaded file is not a valid PPTX presentation") from exc

        if len(presentation.slides) == 0:
            raise ValueError("PPT template must contain at least one slide")

        target_dir = self.template_dir(user_id, template_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = self.template_path(user_id, template_id)
        target_path.write_bytes(content)
        return target_path, presentation

    def delete(self, user_id: uuid.UUID, template_id: uuid.UUID) -> None:
        shutil.rmtree(self.template_dir(user_id, template_id), ignore_errors=True)


class UploadedTemplateService:
    def __init__(self, storage: UserTemplateStorage | None = None) -> None:
        self.storage = storage or UserTemplateStorage()

    async def upload_template(
        self,
        db_session: AsyncSession,
        user_id: uuid.UUID,
        upload_file: UploadFile,
        display_name: str | None = None,
    ) -> UserTemplateUploadResponse:
        content = await upload_file.read()
        template_id = uuid.uuid4()
        original_filename = upload_file.filename or "template.pptx"
        template_key = template_key_for_id(template_id)

        target_path: Path | None = None
        try:
            target_path, presentation = self.storage.save(user_id, template_id, original_filename, content)
            profile = profile_presentation_template(presentation)
            profile_response = _profile_response(profile)
            name = (display_name or Path(original_filename).stem).strip() or "Uploaded Template"
            model = PresentationTemplateModel(
                id=template_id,
                user_id=user_id,
                name=name[:255],
                original_filename=original_filename[:500],
                file_path=str(target_path),
                file_size=len(content),
                content_type=upload_file.content_type or PPTX_CONTENT_TYPE,
                file_hash=hashlib.sha256(content).hexdigest(),
                template_key=template_key,
                slide_count=profile.slide_count,
                status=profile.status,
                role_profile=_profile_dict(profile),
                warnings=profile.warnings,
                is_deleted=False,
            )
            db_session.add(model)
            await db_session.commit()
            await db_session.refresh(model)
            return UserTemplateUploadResponse(
                id=model.id,
                template_key=model.template_key,
                name=model.name,
                original_filename=model.original_filename,
                file_size=model.file_size,
                profile=profile_response,
            )
        except Exception:
            if target_path is not None:
                self.storage.delete(user_id, template_id)
            raise

    async def list_templates(self, db_session: AsyncSession, user_id: uuid.UUID) -> list[Template]:
        statement = (
            select(PresentationTemplateModel)
            .where(PresentationTemplateModel.user_id == user_id)
            .where(PresentationTemplateModel.is_deleted.is_(False))
            .order_by(PresentationTemplateModel.create_time.desc())
        )
        result = await db_session.execute(statement)
        models = result.scalars().all()
        return [self.to_template_response(model) for model in models]

    async def get_template(
        self, db_session: AsyncSession, user_id: uuid.UUID, template_key: str
    ) -> PresentationTemplateModel | None:
        template_id = parse_user_template_key(template_key)
        if template_id is None:
            return None
        statement = (
            select(PresentationTemplateModel)
            .where(PresentationTemplateModel.id == template_id)
            .where(PresentationTemplateModel.user_id == user_id)
            .where(PresentationTemplateModel.is_deleted.is_(False))
        )
        result = await db_session.execute(statement)
        return result.scalar_one_or_none()

    async def delete_template(
        self, db_session: AsyncSession, user_id: uuid.UUID, template_key: str
    ) -> UserTemplateDeleteResponse:
        model = await self.get_template(db_session, user_id, template_key)
        if model is None:
            raise FileNotFoundError("Uploaded template not found")
        model.is_deleted = True
        db_session.add(model)
        await db_session.commit()
        self.storage.delete(user_id, model.id)
        return UserTemplateDeleteResponse(template_key=template_key)

    def to_template_response(self, model: PresentationTemplateModel) -> Template:
        profile = TemplateProfileResponse(**model.role_profile)
        return Template(
            id=model.template_key,
            name=model.name,
            thumbnail=None,
            source=TemplateSource.USER,
            profile_status=model.status,
            role_profile=profile,
        )


uploaded_template_service = UploadedTemplateService()
