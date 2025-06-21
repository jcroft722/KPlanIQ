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
    
    # Fix-related columns added by migration
    has_fixes_applied = Column(Boolean, default=False)
    fix_session_count = Column(Integer, default=0)
    last_fix_applied = Column(DateTime, nullable=True)
    backup_file_path = Column(String(500), nullable=True)

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
    issue_type = Column(String(20))  # Changed from Enum to String to match validation_engine
    severity = Column(String(10))    # Added length constraint
    category = Column(String(50))    # Added length constraint
    title = Column(String(200))      # Added length constraint
    description = Column(Text)       # Changed from String to Text for longer descriptions
    affected_rows = Column(JSON, nullable=True)
    affected_employees = Column(Integer, default=0)  # FIXED: Changed from JSON to Integer
    suggested_action = Column(Text, nullable=True)   # Changed from String to Text
    auto_fixable = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    confidence_score = Column(Numeric(5, 2), nullable=True)  # Changed from Float to Numeric for precision
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Use timezone-aware
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())        # Added updated_at
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)  # Changed from String to Text
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Added FK constraint

    # Relationships
    file_upload = relationship("FileUpload", back_populates="validation_results")
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])  # Added relationship

class DataQualityScore(Base):
    __tablename__ = "data_quality_scores"

    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    overall_score = Column(Numeric(5, 2))      # Changed from Float to Numeric
    completeness_score = Column(Numeric(5, 2)) # Changed from Float to Numeric
    consistency_score = Column(Numeric(5, 2))  # Changed from Float to Numeric
    accuracy_score = Column(Numeric(5, 2))     # Changed from Float to Numeric
    critical_issues = Column(Integer, default=0)
    warning_issues = Column(Integer, default=0)
    anomaly_issues = Column(Integer, default=0)  # This was "info_issues" in validation_engine
    total_issues = Column(Integer, default=0)
    auto_fixable_issues = Column(Integer, default=0)
    auto_fixed_issues = Column(Integer, default=0)  # Add this field
    analysis_version = Column(String(20), default="1.0")  # Add this field
    
    # Fix-related columns added by migration
    resolved_issues = Column(Integer, default=0)
    auto_fixed = Column(Integer, default=0)
    can_proceed_to_compliance = Column(Boolean, default=False)
    blocking_issues = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Fix relationship name to match FileUpload
    file_upload = relationship("FileUpload", back_populates="data_quality_scores")

class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    status = Column(String(20), default="running")
    validation_config = Column(JSON)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_seconds = Column(Numeric(8, 2), nullable=True)
    total_issues_found = Column(Integer, default=0)
    data_quality_score = Column(Numeric(5, 2), nullable=True)
    can_proceed_to_compliance = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # ADD THIS LINE

    file_upload = relationship("FileUpload", back_populates="validation_runs")

# Fix-related models
class FixHistory(Base):
    __tablename__ = "fix_history"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    validation_result_id = Column(Integer, ForeignKey("validation_results.id"))
    session_id = Column(Integer, ForeignKey("fix_sessions.id"), nullable=True)
    fix_type = Column(String(50))  # 'auto_fix', 'manual_entry', 'exclude', 'accept'
    fix_data = Column(JSON, nullable=True)
    applied_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    rollback_data = Column(JSON, nullable=True)  # Store original data for potential rollback
    
    # Relationships
    file_upload = relationship("FileUpload")
    validation_result = relationship("ValidationResult")
    user = relationship("User")
    session = relationship("FixSession")

class FixSession(Base):
    __tablename__ = "fix_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"))
    session_name = Column(String(200))
    description = Column(Text, nullable=True)
    status = Column(String(20), default="active")  # 'active', 'completed', 'cancelled'
    started_by = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_issues = Column(Integer, default=0)
    fixed_issues = Column(Integer, default=0)
    session_data = Column(JSON, nullable=True)  # Store session state
    
    # Relationships
    file_upload = relationship("FileUpload")
    user = relationship("User")

class FixTemplate(Base):
    __tablename__ = "fix_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50))  # 'auto_fix', 'manual_entry', 'exclusion'
    category = Column(String(50))  # 'format_error', 'missing_data', 'anomaly'
    fix_rules = Column(JSON)  # Store the fix logic/rules
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")