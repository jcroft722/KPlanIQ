import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.core.database import DATABASE_URL

def confirm_connection():
    print(f"Database URL: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    try:
        connection = engine.connect()
        print("Connection successful!")
        connection.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    confirm_connection() 