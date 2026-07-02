"""add version app

Revision ID: 5c8d9d5efdeb
Revises: 1a55c8d36887
Create Date: 2026-06-29 14:37:06.170244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c8d9d5efdeb'
down_revision: Union[str, Sequence[str], None] = '1a55c8d36887'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("app", sa.Column("version", sa.String, nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("app", "version")
