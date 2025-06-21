from app.core.database import Base, engine, DATABASE_URL
from app.models.models import User, Project, FileUpload, MappingTemplate, ProcessingJob, EmployeeData, RawEmployeeData, ColumnMapping, ComplianceTestRun, ComplianceTestResult, ValidationResult, DataQualityScore, ValidationRun, FixHistory, FixSession, FixTemplate
from sqlalchemy import inspect, text
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

def create_tables():
    """Create all database tables"""
    print("\nDatabase Configuration:")
    print(f"Database URL: {mask_url(DATABASE_URL)}")
    
    try:
        print("\nCreating database tables...")
        
        # Drop all tables first to ensure clean state
        print("Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        
        # Create all tables
        print("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("\nCreated tables:")
        for table in tables:
            print(f"- {table}")
            # Print columns for each table
            columns = inspector.get_columns(table)
            for column in columns:
                print(f"  - {column['name']}: {column['type']}")
        
        # Specifically check file_uploads
        if 'file_uploads' in tables:
            print("\nfile_uploads table created successfully!")
        else:
            print("\nERROR: file_uploads table was not created!")
            
    except Exception as e:
        print(f"\nERROR: Failed to create tables: {str(e)}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database 'kplan' exists")
        print("3. User has proper permissions")
        print("4. Database URL is correct in .env file")

if __name__ == "__main__":
    create_tables()
    print("\nDatabase table creation completed!") 