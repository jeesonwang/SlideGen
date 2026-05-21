"""Add user presentation templates

Revision ID: 20260521_user_templates
Revises: 508927af516d
Create Date: 2026-05-21 00:00:00.000000+08:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision: str = "20260521_user_templates"
down_revision: Union[str, Sequence[str], None] = "508927af516d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "presentation_templates",
        sa.Column("create_time", sa.DateTime(), nullable=False, comment="Create time"),
        sa.Column("update_time", sa.DateTime(), nullable=False, comment="Update time"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("original_filename", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("file_path", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column("file_hash", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
        sa.Column("template_key", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("slide_count", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("role_profile", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        comment="User uploaded PPTX templates",
    )
    op.create_index(op.f("ix_presentation_templates_create_time"), "presentation_templates", ["create_time"])
    op.create_index(op.f("ix_presentation_templates_file_hash"), "presentation_templates", ["file_hash"])
    op.create_index(op.f("ix_presentation_templates_id"), "presentation_templates", ["id"])
    op.create_index(op.f("ix_presentation_templates_is_deleted"), "presentation_templates", ["is_deleted"])
    op.create_index(op.f("ix_presentation_templates_status"), "presentation_templates", ["status"])
    op.create_index(op.f("ix_presentation_templates_template_key"), "presentation_templates", ["template_key"], unique=True)
    op.create_index(op.f("ix_presentation_templates_update_time"), "presentation_templates", ["update_time"])
    op.create_index(op.f("ix_presentation_templates_user_id"), "presentation_templates", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_presentation_templates_user_id"), table_name="presentation_templates")
    op.drop_index(op.f("ix_presentation_templates_update_time"), table_name="presentation_templates")
    op.drop_index(op.f("ix_presentation_templates_template_key"), table_name="presentation_templates")
    op.drop_index(op.f("ix_presentation_templates_status"), table_name="presentation_templates")
    op.drop_index(op.f("ix_presentation_templates_is_deleted"), table_name="presentation_templates")
    op.drop_index(op.f("ix_presentation_templates_id"), table_name="presentation_templates")
    op.drop_index(op.f("ix_presentation_templates_file_hash"), table_name="presentation_templates")
    op.drop_index(op.f("ix_presentation_templates_create_time"), table_name="presentation_templates")
    op.drop_table("presentation_templates")
