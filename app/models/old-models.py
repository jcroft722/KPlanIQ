from sqlalchemy import Column, Integer, String, Float, Date, Boolean, DateTime, JSON, ForeignKey, Text, Numeric, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

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
    validation_results = relationship("ValidationResult", back_populates="file_upload", cascade="all, delete")
    data_quality_score = relationship("DataQualityScore", back_populates="file_upload", uselist=False, cascade="all, delete")
    validation_runs = relationship("ValidationRun", back_populates="file_upload", cascade="all, delete")


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


class ValidationResult(Base):
    """
    Store comprehensive validation results for uploaded files
    Integrates with existing FileUpload model
    """
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    
    # Issue classification
    issue_type = Column(String(20), nullable=False)  # 'critical', 'warning', 'anomaly'
    severity = Column(String(10), nullable=False)    # 'high', 'medium', 'low'
    category = Column(String(50), nullable=False)    # 'missing_data', 'format_error', etc.
    
    # Issue details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    
    # Affected data
    affected_rows = Column(JSON)  # List of row indices
    affected_employees = Column(Integer, default=0)
    
    # Fix information
    auto_fixable = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Quality metrics
    confidence_score = Column(Numeric(5, 2), default=1.0)  # 0.0 - 1.0
    
    # Additional details (JSON for flexibility)
    details = Column(JSON)  # Store field-specific details, thresholds, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    file_upload = relationship("FileUpload", back_populates="validation_results")
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_validation_file_type', 'file_upload_id', 'issue_type'),
        Index('idx_validation_severity', 'severity'),
        Index('idx_validation_resolved', 'is_resolved'),
    )

class DataQualityScore(Base):
    """
    Store overall data quality metrics for files
    Calculated by ValidationEngine
    """
    __tablename__ = "data_quality_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    
    # Overall quality metrics (0-100 scale)
    overall_score = Column(Numeric(5, 2), nullable=False)
    completeness_score = Column(Numeric(5, 2), nullable=False)
    consistency_score = Column(Numeric(5, 2), nullable=False)
    accuracy_score = Column(Numeric(5, 2), nullable=False)
    
    # Issue counts
    critical_issues = Column(Integer, default=0)
    warning_issues = Column(Integer, default=0)
    anomaly_issues = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    
    # Auto-fix statistics
    auto_fixable_issues = Column(Integer, default=0)
    auto_fixed_issues = Column(Integer, default=0)
    
    # Metadata
    analysis_version = Column(String(20), default="1.0")  # Track validation engine version
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    file_upload = relationship("FileUpload", back_populates="data_quality_score")

class ValidationRun(Base):
    """
    Track validation runs for audit purposes
    Links multiple ValidationResults together
    """
    __tablename__ = "validation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_upload_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    
    # Run details
    status = Column(String(20), default="running")  # 'running', 'completed', 'failed'
    total_issues_found = Column(Integer, default=0)
    processing_time_seconds = Column(Numeric(8, 2))
    
    # Configuration
    validation_config = Column(JSON)  # Store validation settings used
    
    # Results summary
    data_quality_score = Column(Numeric(5, 2))
    can_proceed_to_compliance = Column(Boolean, default=False)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    file_upload = relationship("FileUpload", back_populates="validation_runs")
class ValidationResult(Base):
    __tablename__ = "validation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    
    # Existing fields...
    issue_type = Column(String(50), nullable=False)  # critical, warning, info
    severity = Column(String(20), nullable=False)    # high, medium, low
    category = Column(String(50), nullable=False)    # Missing Data, Format Error, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    affected_rows = Column(JSON)  # List of row indices
    affected_employees = Column(JSON)  # List of employee names/IDs
    suggested_action = Column(Text)
    
    auto_fixable = Column(Boolean, default=False)
    confidence_score = Column(Float, default=0.0)
    details = Column(JSON)  # Additional issue details
    
    # New fields for fix tracking
    is_resolved = Column(Boolean, default=False)
    resolution_method = Column(String(50))  # auto_fix, manual_entry, exclude, accept
    resolution_data = Column(JSON)  # Data used in the fix
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    file_upload = relationship("FileUpload", back_populates="validation_results")
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])

# New model for tracking fix history/audit trail
class FixHistory(Base):
    __tablename__ = "fix_history"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    issue_id = Column(Integer, ForeignKey("validation_results.id"), nullable=False)
    
    action_type = Column(String(50), nullable=False)  # fix_applied, fix_undone, status_changed
    action_data = Column(JSON)  # Details of the action
    
    # Before/after state for undo functionality
    before_state = Column(JSON)
    after_state = Column(JSON)
    
    # User who performed the action
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional metadata
    notes = Column(Text)
    ip_address = Column(String(45))  # For audit purposes
    
    # Relationships
    file_upload = relationship("FileUpload")
    validation_result = relationship("ValidationResult")
    user = relationship("User")

# New model for tracking fix sessions/progress
class FixSession(Base):
    __tablename__ = "fix_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session metadata
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Progress tracking
    total_issues = Column(Integer, default=0)
    resolved_issues = Column(Integer, default=0)
    session_data = Column(JSON)  # Store session state, filters, etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    file_upload = relationship("FileUpload")
    user = relationship("User")

# Update existing FileUpload model to include fix-related fields
class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Existing fields...
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Processing status
    status = Column(String(50), default="uploaded")  # uploaded, validated, fixing, fixed, ready
    
    # Fix-related fields
    has_fixes_applied = Column(Boolean, default=False)
    fix_session_count = Column(Integer, default=0)
    last_fix_applied = Column(DateTime)
    
    # Backup file path (for undo functionality)
    backup_file_path = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="file_uploads")
    validation_results = relationship("ValidationResult", back_populates="file_upload", cascade="all, delete-orphan")
    data_quality_scores = relationship("DataQualityScore", back_populates="file_upload", cascade="all, delete-orphan")

# Update existing DataQualityScore model
class DataQualityScore(Base):
    __tablename__ = "data_quality_scores"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    
    # Overall scores
    overall = Column(Float, nullable=False)
    completeness = Column(Float, default=0.0)
    consistency = Column(Float, default=0.0)
    accuracy = Column(Float, default=0.0)
    
    # Issue counts
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    warning_issues = Column(Integer, default=0)
    info_issues = Column(Integer, default=0)
    resolved_issues = Column(Integer, default=0)
    
    # Auto-fix statistics
    auto_fixable = Column(Integer, default=0)
    auto_fixed = Column(Integer, default=0)
    
    # Compliance readiness
    can_proceed_to_compliance = Column(Boolean, default=False)
    blocking_issues = Column(Integer, default=0)
    
    # Anomaly detection
    anomaly_count = Column(Integer, default=0)
    anomaly_score = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    file_upload = relationship("FileUpload", back_populates="data_quality_scores")

# New model for storing fix templates/presets
class FixTemplate(Base):
    __tablename__ = "fix_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Template metadata
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # ssn_fixes, date_fixes, compensation_fixes, etc.
    
    # Template configuration
    template_data = Column(JSON, nullable=False)  # Fix configuration and rules
    applicable_issue_types = Column(JSON)  # Which issue types this template applies to
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # Sharing and visibility
    is_public = Column(Boolean, default=False)
    is_system_template = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    creator = relationship("User")

# Existing User model (for reference)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True)
    full_name = Column(String(255))
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Role and permissions
    role = Column(String(50), default="user")  # user, admin, tpa_analyst, plan_sponsor
    permissions = Column(JSON)
    
    # Profile
    company_name = Column(String(255))
    phone = Column(String(20))
    
    # Settings
    preferences = Column(JSON)  # User preferences for fixes, notifications, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    file_uploads = relationship("FileUpload", back_populates="user")

#