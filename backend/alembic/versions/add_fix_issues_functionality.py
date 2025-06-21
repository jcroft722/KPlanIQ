"""add_fix_issues_functionality

Revision ID: add_fix_issues_001
Revises: add_resolution_fields
Create Date: 2024-12-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_fix_issues_001'
down_revision = 'add_resolution_fields'
branch_labels = None
depends_on = None


def upgrade():
    """Add Fix Issues functionality to the database."""
    
    # Add new columns to validation_results table
    print("Adding new columns to validation_results table...")
    # op.add_column('validation_results', sa.Column('is_resolved', sa.Boolean(), nullable=True, default=False))
    # op.add_column('validation_results', sa.Column('resolution_method', sa.String(length=50), nullable=True))
    # op.add_column('validation_results', sa.Column('resolution_data', sa.JSON(), nullable=True))
    # op.add_column('validation_results', sa.Column('resolved_by', sa.Integer(), nullable=True))
    # op.add_column('validation_results', sa.Column('resolved_at', sa.DateTime(), nullable=True))
    
    # Add foreign key constraint for resolved_by
    # op.create_foreign_key('fk_validation_results_resolved_by', 'validation_results', 'users', ['resolved_by'], ['id'])
    
    # Add new columns to file_uploads table
    print("Adding new columns to file_uploads table...")
    op.add_column('file_uploads', sa.Column('has_fixes_applied', sa.Boolean(), nullable=True, default=False))
    op.add_column('file_uploads', sa.Column('fix_session_count', sa.Integer(), nullable=True, default=0))
    op.add_column('file_uploads', sa.Column('last_fix_applied', sa.DateTime(), nullable=True))
    op.add_column('file_uploads', sa.Column('backup_file_path', sa.String(length=500), nullable=True))
    
    # Add new columns to data_quality_scores table
    print("Adding new columns to data_quality_scores table...")
    op.add_column('data_quality_scores', sa.Column('resolved_issues', sa.Integer(), nullable=True, default=0))
    op.add_column('data_quality_scores', sa.Column('auto_fixed', sa.Integer(), nullable=True, default=0))
    op.add_column('data_quality_scores', sa.Column('can_proceed_to_compliance', sa.Boolean(), nullable=True, default=False))
    op.add_column('data_quality_scores', sa.Column('blocking_issues', sa.Integer(), nullable=True, default=0))
    
    # Create fix_history table
    print("Creating fix_history table...")
    op.create_table('fix_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('issue_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('action_data', sa.JSON(), nullable=True),
        sa.Column('before_state', sa.JSON(), nullable=True),
        sa.Column('after_state', sa.JSON(), nullable=True),
        sa.Column('performed_by', sa.Integer(), nullable=False),
        sa.Column('performed_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['file_id'], ['file_uploads.id'], ),
        sa.ForeignKeyConstraint(['issue_id'], ['validation_results.id'], ),
        sa.ForeignKeyConstraint(['performed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fix_history_file_id'), 'fix_history', ['file_id'], unique=False)
    op.create_index(op.f('ix_fix_history_issue_id'), 'fix_history', ['issue_id'], unique=False)
    op.create_index(op.f('ix_fix_history_performed_by'), 'fix_history', ['performed_by'], unique=False)
    op.create_index(op.f('ix_fix_history_performed_at'), 'fix_history', ['performed_at'], unique=False)
    
    # Create fix_sessions table
    print("Creating fix_sessions table...")
    op.create_table('fix_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_issues', sa.Integer(), nullable=True, default=0),
        sa.Column('resolved_issues', sa.Integer(), nullable=True, default=0),
        sa.Column('session_data', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True, default=False),
        sa.ForeignKeyConstraint(['file_id'], ['file_uploads.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fix_sessions_file_id'), 'fix_sessions', ['file_id'], unique=False)
    op.create_index(op.f('ix_fix_sessions_user_id'), 'fix_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_fix_sessions_is_active'), 'fix_sessions', ['is_active'], unique=False)
    
    # Create fix_templates table
    print("Creating fix_templates table...")
    op.create_table('fix_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('template_data', sa.JSON(), nullable=False),
        sa.Column('applicable_issue_types', sa.JSON(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0),
        sa.Column('success_rate', sa.Float(), nullable=True, default=0.0),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_system_template', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fix_templates_created_by'), 'fix_templates', ['created_by'], unique=False)
    op.create_index(op.f('ix_fix_templates_category'), 'fix_templates', ['category'], unique=False)
    op.create_index(op.f('ix_fix_templates_is_public'), 'fix_templates', ['is_public'], unique=False)
    
    # Update existing records with default values
    print("Updating existing records with default values...")
    
    # Set default values for new boolean columns
    op.execute("UPDATE validation_results SET is_resolved = FALSE WHERE is_resolved IS NULL")
    op.execute("UPDATE file_uploads SET has_fixes_applied = FALSE WHERE has_fixes_applied IS NULL")
    op.execute("UPDATE file_uploads SET fix_session_count = 0 WHERE fix_session_count IS NULL")
    op.execute("UPDATE data_quality_scores SET resolved_issues = 0 WHERE resolved_issues IS NULL")
    op.execute("UPDATE data_quality_scores SET auto_fixed = 0 WHERE auto_fixed IS NULL")
    op.execute("UPDATE data_quality_scores SET can_proceed_to_compliance = FALSE WHERE can_proceed_to_compliance IS NULL")
    op.execute("UPDATE data_quality_scores SET blocking_issues = 0 WHERE blocking_issues IS NULL")
    op.execute("UPDATE fix_sessions SET is_active = TRUE WHERE is_active IS NULL")
    op.execute("UPDATE fix_sessions SET is_completed = FALSE WHERE is_completed IS NULL")
    op.execute("UPDATE fix_templates SET is_public = FALSE WHERE is_public IS NULL")
    op.execute("UPDATE fix_templates SET is_system_template = FALSE WHERE is_system_template IS NULL")
    
    # Make the boolean columns non-nullable now that they have values
    op.alter_column('validation_results', 'is_resolved', nullable=False)
    op.alter_column('file_uploads', 'has_fixes_applied', nullable=False)
    op.alter_column('file_uploads', 'fix_session_count', nullable=False)
    op.alter_column('data_quality_scores', 'resolved_issues', nullable=False)
    op.alter_column('data_quality_scores', 'auto_fixed', nullable=False)
    op.alter_column('data_quality_scores', 'can_proceed_to_compliance', nullable=False)
    op.alter_column('data_quality_scores', 'blocking_issues', nullable=False)
    op.alter_column('fix_sessions', 'is_active', nullable=False)
    op.alter_column('fix_sessions', 'is_completed', nullable=False)
    op.alter_column('fix_templates', 'is_public', nullable=False)
    op.alter_column('fix_templates', 'is_system_template', nullable=False)
    
    print("Fix Issues functionality migration completed successfully!")


def downgrade():
    """Remove Fix Issues functionality from the database."""
    
    print("WARNING: This will remove all Fix Issues data permanently!")
    
    # Drop the new tables
    print("Dropping fix_templates table...")
    op.drop_index(op.f('ix_fix_templates_is_public'), table_name='fix_templates')
    op.drop_index(op.f('ix_fix_templates_category'), table_name='fix_templates')
    op.drop_index(op.f('ix_fix_templates_created_by'), table_name='fix_templates')
    op.drop_table('fix_templates')
    
    print("Dropping fix_sessions table...")
    op.drop_index(op.f('ix_fix_sessions_is_active'), table_name='fix_sessions')
    op.drop_index(op.f('ix_fix_sessions_user_id'), table_name='fix_sessions')
    op.drop_index(op.f('ix_fix_sessions_file_id'), table_name='fix_sessions')
    op.drop_table('fix_sessions')
    
    print("Dropping fix_history table...")
    op.drop_index(op.f('ix_fix_history_performed_at'), table_name='fix_history')
    op.drop_index(op.f('ix_fix_history_performed_by'), table_name='fix_history')
    op.drop_index(op.f('ix_fix_history_issue_id'), table_name='fix_history')
    op.drop_index(op.f('ix_fix_history_file_id'), table_name='fix_history')
    op.drop_table('fix_history')
    
    # Remove columns from data_quality_scores
    print("Removing columns from data_quality_scores table...")
    op.drop_column('data_quality_scores', 'blocking_issues')
    op.drop_column('data_quality_scores', 'can_proceed_to_compliance')
    op.drop_column('data_quality_scores', 'auto_fixed')
    op.drop_column('data_quality_scores', 'resolved_issues')
    
    # Remove columns from file_uploads
    print("Removing columns from file_uploads table...")
    op.drop_column('file_uploads', 'backup_file_path')
    op.drop_column('file_uploads', 'last_fix_applied')
    op.drop_column('file_uploads', 'fix_session_count')
    op.drop_column('file_uploads', 'has_fixes_applied')
    
    # Remove foreign key and columns from validation_results
    print("Removing columns from validation_results table...")
    # op.drop_constraint('fk_validation_results_resolved_by', 'validation_results', type_='foreignkey')
    # op.drop_column('validation_results', 'resolved_at')
    # op.drop_column('validation_results', 'resolved_by')
    # op.drop_column('validation_results', 'resolution_data')
    # op.drop_column('validation_results', 'resolution_method')
    # op.drop_column('validation_results', 'is_resolved')
    
    print("Fix Issues functionality migration rollback completed!")