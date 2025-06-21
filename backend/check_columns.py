from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'validation_results' ORDER BY column_name"))
    print("Validation results columns:")
    for row in result.fetchall():
        print(f"- {row[0]}") 