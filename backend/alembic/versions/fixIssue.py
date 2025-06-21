# Database migration script for adding new fields

## Alembic migration script:

revision = 'add_fix_functionality'
down_revision = 'previous_revision'

def upgrade():
    # Add new columns to validation_results
    op.add_column('validation_results', sa.Column('is_resolved', sa.Boolean(), default=False))
    op.add_column('validation_results', sa.Column('resolution_method', sa.String(50)))
    op.add_column('validation_results', sa.Column('resolution_data', sa.JSON()))
    op.add_column('validation_results', sa.Column('resolved_by', sa.Integer(), sa.ForeignKey('users.id')))
    op.add_column('validation_results', sa.Column('resolved_at', sa.DateTime()))
    
    # Add new columns to file_uploads
    op.add_column('file_uploads', sa.Column('has_fixes_applied', sa.Boolean(), default=False))
    op.add_column('file_uploads', sa.Column('fix_session_count', sa.Integer(), default=0))
    op.add_column('file_uploads', sa.Column('last_fix_applied', sa.DateTime()))
    op.add_column('file_uploads', sa.Column('backup_file_path', sa.String(500)))
    
    # Add new columns to data_quality_scores
    op.add_column('data_quality_scores', sa.Column('resolved_issues', sa.Integer(), default=0))
    op.add_column('data_quality_scores', sa.Column('auto_fixed', sa.Integer(), default=0))
    op.add_column('data_quality_scores', sa.Column('can_proceed_to_compliance', sa.Boolean(), default=False))
    op.add_column('data_quality_scores', sa.Column('blocking_issues', sa.Integer(), default=0))
    
    # Create new tables
    op.create_table('fix_history', ...)
    op.create_table('fix_sessions', ...)
    op.create_table('fix_templates', ...)

def downgrade():
    # Remove added columns and tables
    op.drop_table('fix_templates')
    op.drop_table('fix_sessions') 
    op.drop_table('fix_history')
    # ... remove columns
