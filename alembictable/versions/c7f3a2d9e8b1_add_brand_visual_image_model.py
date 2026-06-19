"""add brand visual image model

Revision ID: c7f3a2d9e8b1
Revises: b9a17d6e3c42
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7f3a2d9e8b1"
down_revision: Union[str, None] = "b9a17d6e3c42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "brand_visuals",
        sa.Column(
            "image_model",
            sa.String(length=100),
            server_default="wan2.6-image",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("brand_visuals", "image_model")
