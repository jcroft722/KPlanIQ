"""add resolution fields

Revision ID: add_resolution_fields
Revises: 
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_resolution_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add resolved_at and resolution_notes columns to validation_results table
    op.add_column('validation_results', sa.Column('resolved_at', sa.DateTime(), nullable=True))
    op.add_column('validation_results', sa.Column('resolution_notes', sa.String(), nullable=True))
    # Add updated_at column to validation_results table
    op.add_column('validation_results', sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()))


def downgrade() -> None:
    # Remove the columns if needed to rollback
    op.drop_column('validation_results', 'resolution_notes')
    op.drop_column('validation_results', 'resolved_at') 