from app.core.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    row = result.fetchone()
    if row:
        print(f"Current alembic version: {row[0]}")
    else:
        print("No alembic version found") 