import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from app.core.database import DATABASE_URL

def check_table_schema(table_name: str):
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Get columns for the specified table
    columns = inspector.get_columns(table_name)
    print(f"\n{table_name} Table Schema:")
    print("-" * 50)
    for column in columns:
        print(f"Column: {column['name']}")
        print(f"Type: {column['type']}")
        print(f"Nullable: {column['nullable']}")
        print(f"Default: {column.get('default')}")
        print(f"Onupdate: {column.get('onupdate')}")
        print("-" * 30)

def main():
    check_table_schema('validation_results')
    check_table_schema('validation_runs')

if __name__ == "__main__":
    main() 