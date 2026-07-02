"""add visual quota refund flags

Revision ID: 8d42f6b1c9e3
Revises: 7c91e4a2b6d0
Create Date: 2026-06-23 10:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8d42f6b1c9e3"
down_revision: Union[str, None] = "7c91e4a2b6d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("brand_kits", sa.Column("quota_refunded", sa.Boolean(), server_default="0", nullable=False))
    op.add_column("brand_visuals", sa.Column("quota_refunded", sa.Boolean(), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("brand_visuals", "quota_refunded")
    op.drop_column("brand_kits", "quota_refunded")
