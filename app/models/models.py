from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer)
    file_path = Column(String)
    mime_type = Column(String)
    status = Column(String)  # 'uploaded', 'processed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    row_count = Column(Integer)
    column_count = Column(Integer)
    headers = Column(JSON)  # Store headers as JSON array

    # Relationships
    raw_data = relationship("RawEmployeeData", back_populates="file_upload", cascade="all, delete")
    employee_data = relationship("EmployeeData", back_populates="file_upload", cascade="all, delete")
    column_mappings = relationship("ColumnMapping", back_populates="file_upload", cascade="all, delete")

class RawEmployeeData(Base):
    __tablename__ = "raw_employee_data"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey('file_uploads.id', ondelete='CASCADE'))
    row_data = Column(JSON)  # Store raw row data as JSON
    mapped_record_id = Column(Integer, ForeignKey('employee_data.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    file_upload = relationship("FileUpload", back_populates="raw_data")
    mapped_record = relationship("EmployeeData", foreign_keys=[mapped_record_id], back_populates="raw_records")

class EmployeeData(Base):
    __tablename__ = "employee_data"

    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey('file_uploads.id', ondelete='CASCADE'))
    ssn = Column(String, index=True)
    eeid = Column(String, index=True)
    first_name = Column(String)
    last_name = Column(String)
    dob = Column(Date)
    doh = Column(Date)  # Date of Hire
    dot = Column(Date)  # Date of Termination
    hours_worked = Column(Float)
    ownership_percentage = Column(Float)
    is_officer = Column(Boolean)
    prior_year_compensation = Column(Float)
    employee_deferrals = Column(Float)
    employer_match = Column(Float)
    employer_profit_sharing = Column(Float)
    employer_sh_contribution = Column(Float)

    # Relationships
    file_upload = relationship("FileUpload", back_populates="employee_data")
    raw_records = relationship("RawEmployeeData", back_populates="mapped_record")

class ComplianceTest(Base):
    __tablename__ = "compliance_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey('file_uploads.id', ondelete='CASCADE'))
    test_name = Column(String)
    status = Column(String)  # 'passed', 'failed', 'in_progress'
    run_date = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)  # Store test details as JSON

    # Relationships
    file_upload = relationship("FileUpload")

class ColumnMapping(Base):
    __tablename__ = "column_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey('file_uploads.id', ondelete='CASCADE'))
    source_column = Column(String)
    target_column = Column(String)
    mapping_type = Column(String)  # 'auto_exact', 'auto_fuzzy', 'manual'
    confidence_score = Column(Float)

    # Relationships
    file_upload = relationship("FileUpload", back_populates="column_mappings") 