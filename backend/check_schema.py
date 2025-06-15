import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect
from app.core.database import DATABASE_URL

def check_validation_results_schema():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    
    # Get columns for validation_results table
    columns = inspector.get_columns('validation_results')
    print("\nValidation Results Table Schema:")
    print("-" * 50)
    for column in columns:
        print(f"Column: {column['name']}")
        print(f"Type: {column['type']}")
        print(f"Nullable: {column['nullable']}")
        print(f"Default: {column.get('default')}")
        print(f"Onupdate: {column.get('onupdate')}")
        print("-" * 30)

if __name__ == "__main__":
    check_validation_results_schema() 