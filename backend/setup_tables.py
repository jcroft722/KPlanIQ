from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, JSON, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create declarative base
Base = declarative_base()

# Define User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Define FileUpload model
class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    original_filename = Column(String)
    file_size = Column(Integer)
    file_path = Column(String)
    mime_type = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    row_count = Column(Integer)
    column_count = Column(Integer)
    headers = Column(JSON)

# Define ValidationResult model
class ValidationResult(Base):
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    issue_type = Column(String)
    severity = Column(String)
    category = Column(String)
    title = Column(String)
    description = Column(Text)
    affected_rows = Column(Integer)
    affected_employees = Column(Integer)
    suggested_action = Column(Text)
    auto_fixable = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    confidence_score = Column(Float)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

# Define DataQualityScore model
class DataQualityScore(Base):
    __tablename__ = "data_quality_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    overall_score = Column(Float)
    completeness_score = Column(Float)
    accuracy_score = Column(Float)
    consistency_score = Column(Float)
    timeliness_score = Column(Float)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Define ValidationRun model
class ValidationRun(Base):
    __tablename__ = "validation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    status = Column(String)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    """Create all tables in the correct order"""
    try:
        # Drop all tables first to ensure clean state
        Base.metadata.drop_all(bind=engine)
        
        # Create all tables at once - SQLAlchemy will handle the order
        print("Creating all tables...")
        Base.metadata.create_all(bind=engine)
        
        print("All tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        raise

if __name__ == "__main__":
    print("Starting database setup...")
    create_tables()
    print("Database setup completed!") 