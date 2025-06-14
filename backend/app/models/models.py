from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Boolean, Numeric, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import enum

from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to projects
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    mapping_templates = relationship("MappingTemplate", back_populates="project")

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
    compliance_runs = relationship("ComplianceTestRun", back_populates="file")
    processing_jobs = relationship("ProcessingJob", back_populates="file_upload")
    validation_results = relationship("ValidationResult", back_populates="file_upload")
    data_quality_scores = relationship("DataQualityScore", back_populates="file_upload")
    validation_runs = relationship("ValidationRun", back_populates="file_upload")

class MappingTemplate(Base):
    __tablename__ = "mapping_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    source_schema = Column(JSON)  # Expected source columns
    target_schema = Column(JSON)  # Target schema definition
    mapping_rules = Column(JSON)  # Auto-mapping rules
    validation_rules = Column(JSON)  # Data quality rules
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="mapping_templates")

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    mapping_template_id = Column(Integer, ForeignKey("mapping_templates.id"))
    column_mappings = Column(JSON)  # Applied column mappings
    validation_results = Column(JSON)  # Data quality results
    processed_data_path = Column(String)  # Path to cleaned data
    status = Column(String, default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    
    # Relationships
    file_upload = relationship("FileUpload", back_populates="processing_jobs")

class EmployeeData(Base):
    __tablename__ = "employee_data"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    
    # Employee identification
    ssn = Column(String)
    eeid = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    
    # Dates
    dob = Column(DateTime)
    doh = Column(DateTime)  # Date of Hire
    dot = Column(DateTime)  # Date of Termination
    
    # Work and ownership details
    hours_worked = Column(Numeric(10, 2))
    ownership_percentage = Column(Numeric(5, 2))
    is_officer = Column(Boolean)
    
    # Financial data
    prior_year_comp = Column(Numeric(15, 2))
    employee_deferrals = Column(Numeric(15, 2))
    employer_match = Column(Numeric(15, 2))
    employer_profit_sharing = Column(Numeric(15, 2))
    employer_sh_contribution = Column(Numeric(15, 2))
    
    # Metadata and timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationship to file upload
    file_upload = relationship("FileUpload", back_populates="employee_data")
    raw_record = relationship("RawEmployeeData", back_populates="mapped_record", uselist=False)

class RawEmployeeData(Base):
    __tablename__ = "raw_employee_data"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    row_data = Column(JSON)  # Store the raw row data as JSON
    mapped_record_id = Column(Integer, ForeignKey("employee_data.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    file_upload = relationship("FileUpload", back_populates="raw_data")
    mapped_record = relationship("EmployeeData", back_populates="raw_record")

class ColumnMapping(Base):
    __tablename__ = "column_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    source_column = Column(String, nullable=False)
    target_column = Column(String, nullable=False)
    mapping_type = Column(String)  # manual, auto_exact, auto_fuzzy, auto_semantic
    confidence_score = Column(Numeric(5, 2))  # For auto-mapped columns
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    file_upload = relationship("FileUpload", back_populates="column_mappings")
    user = relationship("User") 


class ComplianceTestRun(Base):
    __tablename__ = "compliance_test_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id"))
    run_date = Column(DateTime, default=datetime.utcnow)
    total_tests = Column(Integer)
    passed_tests = Column(Integer)
    failed_tests = Column(Integer)
    
    # Relationship to file
    file = relationship("FileUpload", back_populates="compliance_runs")
    
    # Relationship to individual test results
    test_results = relationship("ComplianceTestResult", back_populates="test_run")

class ComplianceTestResult(Base):
    __tablename__ = "compliance_test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_run_id = Column(Integer, ForeignKey("compliance_test_runs.id"))
    test_id = Column(String(50))  # e.g., 'min_age', 'adp_test'
    test_name = Column(String(200))
    test_category = Column(String(50))  # 'eligibility', 'limits', etc.
    status = Column(String(20))  # 'passed', 'failed', 'warning'
    message = Column(Text)
    affected_employees = Column(Integer, default=0)
    details = Column(JSON)  # Store additional test details
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to test run
    test_run = relationship("ComplianceTestRun", back_populates="test_results")

class ValidationIssueType(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    issue_type = Column(Enum(ValidationIssueType))
    severity = Column(String)
    category = Column(String)
    title = Column(String)
    description = Column(String)
    affected_rows = Column(JSON, nullable=True)
    affected_employees = Column(JSON, nullable=True)
    suggested_action = Column(String, nullable=True)
    auto_fixable = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    confidence_score = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(String, nullable=True)

    file_upload = relationship("FileUpload", back_populates="validation_results")

class DataQualityScore(Base):
    __tablename__ = "data_quality_scores"

    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    overall_score = Column(Float)
    completeness_score = Column(Float)
    consistency_score = Column(Float)
    accuracy_score = Column(Float)
    critical_issues = Column(Integer, default=0)
    warning_issues = Column(Integer, default=0)
    anomaly_issues = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    auto_fixable_issues = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    file_upload = relationship("FileUpload", back_populates="data_quality_scores")

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    status = Column(String)  # running, completed, failed
    validation_config = Column(JSON)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    total_issues_found = Column(Integer, default=0)
    data_quality_score = Column(Float, nullable=True)
    can_proceed_to_compliance = Column(Boolean, default=False)
    error_message = Column(String, nullable=True)

    file_upload = relationship("FileUpload", back_populates="validation_runs")