"""Add check constraints and reviews_count column

Revision ID: fc27d05dd3d9
Revises: ae1897626871
Create Date: 2026-10-26 14:30:38.970741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column


# revision identifiers, used by Alembic.
revision: str = '997056039043'
down_revision: Union[str, Sequence[str], None] = 'ae1897626871'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint('balance_not_negative', 'users', 'balance >= 0')
    op.create_check_constraint('rating_range', 'apps', 'rating >= 0 AND rating <= 5')
    op.alter_column('apps', 'rating', nullable=False)
    op.add_column('apps', Column('reviews_count', sa.Integer(), nullable=False))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('balance_not_negative', 'users', 'check')
    op.drop_constraint('rating_range', 'apps', 'check')
    op.alter_column('apps', 'rating', nullable=True)
    op.drop_column('apps', 'reviews_count')
    