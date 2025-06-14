import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.core.database import DATABASE_URL
import os
from dotenv import load_dotenv

def test_connection():
    # Extract database name from URL
    db_name = DATABASE_URL.split('/')[-1]
    # Create connection URL without database name
    base_url = DATABASE_URL.rsplit('/', 1)[0]
    
    print(f"\nTesting database connection...")
    print(f"Database name: {db_name}")
    
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(base_url + '/postgres')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()
        
        if not exists:
            print(f"\nDatabase '{db_name}' does not exist. Creating it...")
            cur.execute(f'CREATE DATABASE {db_name}')
            print(f"Database '{db_name}' created successfully!")
        else:
            print(f"\nDatabase '{db_name}' already exists.")
        
        # Close connection to postgres database
        cur.close()
        conn.close()
        
        # Try to connect to the actual database
        print(f"\nTesting connection to '{db_name}'...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute('SELECT version();')
        version = cur.fetchone()
        print(f"Successfully connected to database!")
        print(f"PostgreSQL version: {version[0]}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. User has proper permissions")
        print("3. Database URL is correct in .env file")

if __name__ == "__main__":
    test_connection() 