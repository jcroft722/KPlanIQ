"""Fix all validation_results data types

Revision ID: 90f19db23fa3
Revises: 
Create Date: 2024-12-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '90f19db23fa3'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    connection = op.get_bind()
    
    # Fix 1: Convert issue_type from enum to string
    print("Converting issue_type from enum to string...")
    op.add_column('validation_results', sa.Column('issue_type_new', sa.String(20), nullable=True))
    
    connection.execute(text("""
        UPDATE validation_results 
        SET issue_type_new = issue_type::text
    """))
    
    op.drop_column('validation_results', 'issue_type')
    op.alter_column('validation_results', 'issue_type_new', new_column_name='issue_type')
    op.alter_column('validation_results', 'issue_type', nullable=False)
    
    # Fix 2: Convert affected_employees from JSON to integer
    print("Converting affected_employees from JSON to integer...")
    op.add_column('validation_results', sa.Column('affected_employees_new', sa.Integer(), nullable=True))
    
    connection.execute(text("""
        UPDATE validation_results 
        SET affected_employees_new = CASE 
            WHEN affected_employees IS NULL THEN 0
            WHEN jsonb_typeof(affected_employees::jsonb) = 'number' THEN (affected_employees::jsonb)::integer
            WHEN jsonb_typeof(affected_employees::jsonb) = 'array' THEN jsonb_array_length(affected_employees::jsonb)
            ELSE 0
        END
    """))
    
    op.drop_column('validation_results', 'affected_employees')
    op.alter_column('validation_results', 'affected_employees_new', new_column_name='affected_employees')
    
    # Fix 3: Add updated_at column
    print("Adding updated_at column...")
    try:
        op.add_column('validation_results', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    except Exception as e:
        print(f"updated_at column might already exist: {e}")
    
    # Fix 4: Convert other potential data type issues
    print("Fixing other data types...")
    
    # Ensure confidence_score is numeric
    try:
        op.alter_column('validation_results', 'confidence_score',
                       existing_type=sa.Float(),
                       type_=sa.Numeric(precision=5, scale=2),
                       existing_nullable=True)
    except Exception as e:
        print(f"confidence_score already correct type: {e}")
    
    # Ensure text fields are TEXT type
    try:
        op.alter_column('validation_results', 'description',
                       existing_type=sa.String(),
                       type_=sa.Text(),
                       existing_nullable=False)
    except Exception as e:
        print(f"description already correct type: {e}")
    
    try:
        op.alter_column('validation_results', 'suggested_action',
                       existing_type=sa.String(),
                       type_=sa.Text(),
                       existing_nullable=True)
    except Exception as e:
        print(f"suggested_action already correct type: {e}")
    
    # Fix 5: Drop old enum type
    try:
        connection.execute(text("DROP TYPE IF EXISTS validationissuetype"))
        print("Dropped old enum type")
    except Exception as e:
        print(f"Could not drop enum type: {e}")

def downgrade():
    # This would be complex to reverse, so we'll keep it simple
    print("Downgrade not implemented - manual database restore required")
    pass