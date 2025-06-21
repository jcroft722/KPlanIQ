"""Merge fix_issues and validation_results branches

Revision ID: 766b7f5cbeb2
Revises: 90f19db23fa3, add_fix_issues_001
Create Date: 2025-06-21 12:40:37.953361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '766b7f5cbeb2'
down_revision: Union[str, None] = ('90f19db23fa3', 'add_fix_issues_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
