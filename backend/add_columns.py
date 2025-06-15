from sqlalchemy import create_engine, text

# Create engine
engine = create_engine('postgresql://postgres:Cooper@localhost:5432/kplan')

# SQL to add columns
sql = """
ALTER TABLE validation_results 
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS resolution_notes TEXT;
"""

# Execute SQL
with engine.connect() as connection:
    connection.execute(text(sql))
    connection.commit()

print("Columns added successfully!") 