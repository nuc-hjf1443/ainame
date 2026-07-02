"""add visual quota usage date

Revision ID: d3f4a5b6c7d8
Revises: 8d42f6b1c9e3
Create Date: 2026-06-23 18:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3f4a5b6c7d8"
down_revision: Union[str, None] = "8d42f6b1c9e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("brand_kits", sa.Column("quota_usage_date", sa.Date(), nullable=True))
    op.add_column("brand_visuals", sa.Column("quota_usage_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("brand_visuals", "quota_usage_date")
    op.drop_column("brand_kits", "quota_usage_date")
