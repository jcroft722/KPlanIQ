"""
Create new migration file: alembic/versions/add_validation_system.py
Run: alembic revision --autogenerate -m "Add validation system tables"
"""

migration_template = '''
"""Add validation system tables

Revision ID: add_validation_system
Revises: [previous_revision_id]
Create Date: 2024-06-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_validation_system'
down_revision = '[your_previous_revision_id]'  # Replace with your latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Create validation_results table
    op.create_table('validation_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_upload_id', sa.Integer(), nullable=False),
        sa.Column('issue_type', sa.String(length=20), nullable=False),
        sa.Column('severity', sa.String(length=10), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('suggested_action', sa.Text(), nullable=False),
        sa.Column('affected_rows', sa.JSON(), nullable=True),
        sa.Column('affected_employees', sa.Integer(), nullable=True),
        sa.Column('auto_fixable', sa.Boolean(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['file_upload_id'], ['file_uploads.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_validation_file_type', 'validation_results', ['file_upload_id', 'issue_type'], unique=False)
    op.create_index('idx_validation_resolved', 'validation_results', ['is_resolved'], unique=False)
    op.create_index('idx_validation_severity', 'validation_results', ['severity'], unique=False)
    op.create_index(op.f('ix_validation_results_id'), 'validation_results', ['id'], unique=False)

    # Create data_quality_scores table
    op.create_table('data_quality_scores',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_upload_id', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('completeness_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('consistency_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('accuracy_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('critical_issues', sa.Integer(), nullable=True),
        sa.Column('warning_issues', sa.Integer(), nullable=True),
        sa.Column('anomaly_issues', sa.Integer(), nullable=True),
        sa.Column('total_issues', sa.Integer(), nullable=True),
        sa.Column('auto_fixable_issues', sa.Integer(), nullable=True),
        sa.Column('auto_fixed_issues', sa.Integer(), nullable=True),
        sa.Column('analysis_version', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['file_upload_id'], ['file_uploads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_quality_scores_id'), 'data_quality_scores', ['id'], unique=False)

    # Create validation_runs table
    op.create_table('validation_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_upload_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('total_issues_found', sa.Integer(), nullable=True),
        sa.Column('processing_time_seconds', sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column('validation_config', sa.JSON(), nullable=True),
        sa.Column('data_quality_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('can_proceed_to_compliance', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['file_upload_id'], ['file_uploads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_validation_runs_id'), 'validation_runs', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_validation_runs_id'), table_name='validation_runs')
    op.drop_table('validation_runs')
    
    op.drop_index(op.f('ix_data_quality_scores_id'), table_name='data_quality_scores')
    op.drop_table('data_quality_scores')
    
    op.drop_index('idx_validation_severity', table_name='validation_results')
    op.drop_index('idx_validation_resolved', table_name='validation_results')
    op.drop_index('idx_validation_file_type', table_name='validation_results')
    op.drop_index(op.f('ix_validation_results_id'), table_name='validation_results')
    op.drop_table('validation_results')
'''
