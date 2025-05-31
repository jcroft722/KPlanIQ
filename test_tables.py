from sqlalchemy import create_engine, inspect

# Database URL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Cooper@localhost:5432/kplan"

def main():
    # Create engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create inspector
    inspector = inspect(engine)
    
    # Get all table names
    tables = inspector.get_table_names()
    print("\nTables in database:")
    for table in tables:
        print(f"- {table}")
        
        # Get columns for each table
        columns = inspector.get_columns(table)
        print("  Columns:")
        for column in columns:
            print(f"    - {column['name']}: {column['type']}")
        print()

if __name__ == "__main__":
    main() 