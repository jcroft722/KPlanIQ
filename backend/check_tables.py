from app.core.database import engine, DATABASE_URL
from sqlalchemy import inspect
import os
from dotenv import load_dotenv

def mask_url(url):
    """Mask sensitive information in database URL"""
    if not url:
        return "No DATABASE_URL found"
    parts = url.split('@')
    if len(parts) == 2:
        auth, rest = parts
        return f"{auth.split(':')[0]}:****@{rest}"
    return url

def check_tables():
    print("\nDatabase Configuration:")
    print(f"Database URL: {mask_url(DATABASE_URL)}")
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("\nExisting tables in database:")
        for table in tables:
            print(f"- {table}")
        
        # Check specifically for file_uploads table
        if 'file_uploads' in tables:
            print("\nfile_uploads table exists and has the following columns:")
            columns = inspector.get_columns('file_uploads')
            for column in columns:
                print(f"- {column['name']}: {column['type']}")
        else:
            print("\nWARNING: file_uploads table does not exist!")
    except Exception as e:
        print(f"\nERROR: Failed to connect to database: {str(e)}")

if __name__ == "__main__":
    check_tables() 