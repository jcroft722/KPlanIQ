"""
Advanced Data Validation Engine for KPlanIQ
Integrates with existing FastAPI backend and database models
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
from sqlalchemy.orm import Session
from app.models.models import FileUpload, ValidationResult, EmployeeData

logger = logging.getLogger(__name__)

class IssueType(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class Severity(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Category(Enum):
    MISSING_DATA = "missing_data"
    FORMAT_ERROR = "format_error"
    LOGIC_ERROR = "logic_error"
    COMPLIANCE_ERROR = "compliance_error"
    ANOMALY = "anomaly"

@dataclass
class ValidationIssue:
    """Represents a single validation issue found in the data"""
    id: Optional[int] = None
    file_upload_id: Optional[int] = None
    issue_type: IssueType = IssueType.INFO
    severity: Severity = Severity.LOW
    category: Category = Category.MISSING_DATA
    title: str = ""
    description: str = ""
    affected_rows: List[int] = field(default_factory=list)
    affected_employees: int = 0
    suggested_action: str = ""
    auto_fixable: bool = False
    is_resolved: bool = False
    confidence_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        self.affected_employees = len(set(self.affected_rows))

class DataValidationEngine:
    """
    Comprehensive data validation engine for 401(k) employee census data
    Integrates with existing KPlanIQ database models and API structure
    """
    
    def __init__(self, df: pd.DataFrame, file_upload_id: int, db: Session, historical_data: Optional[pd.DataFrame] = None):
        self.df = df.copy()
        self.file_upload_id = file_upload_id
        self.db = db
        self.historical_data = historical_data
        self.validation_issues: List[ValidationIssue] = []
        self.data_quality_score = 100.0
        
        # Load existing validation results if any
        self.existing_results = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_upload_id
        ).all()
    
    def run_comprehensive_validation(self) -> Tuple[List[ValidationIssue], float]:
        """
        Run all validation checks and return issues with overall quality score
        """
        logger.info(f"Starting comprehensive validation for file {self.file_upload_id}")
        
        # Clear previous results
        self.validation_issues = []
        
        # Critical validation checks (must pass)
        self._validate_required_fields()
        self._validate_data_formats()
        self._validate_cross_field_logic()
        
        # Warning-level checks (should review)
        self._detect_compensation_anomalies()
        self._detect_demographic_inconsistencies()
        self._detect_mass_events()
        
        # Anomaly detection (informational)
        self._detect_statistical_outliers()
        self._detect_pattern_anomalies()
        self._detect_round_number_bias()
        
        # Compliance-specific checks
        self._validate_compliance_readiness()
        
        # Calculate overall data quality score
        self._calculate_data_quality_score()
        
        logger.info(f"Validation complete. Found {len(self.validation_issues)} issues. Quality score: {self.data_quality_score}")
        
        return self.validation_issues, self.data_quality_score
    
    def _validate_required_fields(self):
        """Check for missing critical fields required for compliance testing"""
        required_fields = ['SSN', 'DOB', 'DOH', 'PriorYearComp']
        
        for field in required_fields:
            if field not in self.df.columns:
                self.validation_issues.append(ValidationIssue(
                    issue_type=IssueType.CRITICAL,
                    severity=Severity.HIGH,
                    category=Category.MISSING_DATA,
                    title=f"Missing Required Field: {field}",
                    description=f"The {field} field is required for compliance testing but was not found in the uploaded data.",
                    affected_rows=[],
                    affected_employees=len(self.df),
                    suggested_action=f"Add the {field} column to your data file or map an existing column to {field}.",
                    auto_fixable=False,
                    confidence_score=1.0,
                    details={"field_name": field, "required_for": "compliance_testing"}
                ))
                continue
            
            # Check for missing values in required fields
            null_mask = self.df[field].isnull()
            if null_mask.any():
                null_rows = self.df[null_mask].index.tolist()
                self.validation_issues.append(ValidationIssue(
                    issue_type=IssueType.CRITICAL,
                    severity=Severity.HIGH,
                    category=Category.MISSING_DATA,
                    title=f"Missing Values in {field}",
                    description=f"{len(null_rows)} employees are missing {field} values, which are required for compliance testing.",
                    affected_rows=null_rows,
                    affected_employees=len(null_rows),
                    suggested_action=f"Provide {field} values for all employees or exclude incomplete records.",
                    auto_fixable=False,
                    confidence_score=1.0,
                    details={"field_name": field, "null_count": len(null_rows)}
                ))
    
    def _validate_data_formats(self):
        """Validate data formats and types"""
        
        # Date format validation
        date_fields = ['DOB', 'DOH', 'DOT']
        for field in date_fields:
            if field in self.df.columns:
                self._validate_date_format(field)
        
        # SSN format validation
        if 'SSN' in self.df.columns:
            self._validate_ssn_format()
        
        # Numeric field validation
        numeric_fields = ['PriorYearComp', 'EmployeeDeferrals', 'EmployerMatch', 'HoursWorked']
        for field in numeric_fields:
            if field in self.df.columns:
                self._validate_numeric_format(field)
    
    def _validate_date_format(self, field: str):
        """Validate date field formats"""
        if field not in self.df.columns:
            return
        
        invalid_dates = []
        for idx, value in self.df[field].items():
            if pd.isnull(value):
                continue
            
            try:
                if isinstance(value, str):
                    # Try common date formats
                    pd.to_datetime(value, format='%Y-%m-%d', errors='raise')
                elif not isinstance(value, (datetime, pd.Timestamp)):
                    invalid_dates.append(idx)
            except:
                invalid_dates.append(idx)
        
        if invalid_dates:
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.CRITICAL,
                severity=Severity.HIGH,
                category=Category.FORMAT_ERROR,
                title=f"Invalid Date Format in {field}",
                description=f"{len(invalid_dates)} records have invalid date formats in {field}. Expected format: YYYY-MM-DD.",
                affected_rows=invalid_dates,
                affected_employees=len(invalid_dates),
                suggested_action=f"Convert {field} values to YYYY-MM-DD format.",
                auto_fixable=True,
                confidence_score=0.9,
                details={"field_name": field, "expected_format": "YYYY-MM-DD", "invalid_count": len(invalid_dates)}
            ))
    
    def _validate_ssn_format(self):
        """Validate Social Security Number formats"""
        if 'SSN' not in self.df.columns:
            return
        
        ssn_pattern = re.compile(r'^\d{3}-?\d{2}-?\d{4}$|^\d{9}$')
        invalid_ssns = []
        
        for idx, ssn in self.df['SSN'].items():
            if pd.isnull(ssn):
                continue
            
            ssn_str = str(ssn).strip()
            if not ssn_pattern.match(ssn_str):
                invalid_ssns.append(idx)
        
        if invalid_ssns:
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.CRITICAL,
                severity=Severity.HIGH,
                category=Category.FORMAT_ERROR,
                title="Invalid SSN Format",
                description=f"{len(invalid_ssns)} records have invalid SSN formats. Expected: XXX-XX-XXXX or XXXXXXXXX.",
                affected_rows=invalid_ssns,
                affected_employees=len(invalid_ssns),
                suggested_action="Correct SSN formats to XXX-XX-XXXX or remove hyphens for XXXXXXXXX format.",
                auto_fixable=True,
                confidence_score=0.8,
                details={"expected_formats": ["XXX-XX-XXXX", "XXXXXXXXX"], "invalid_count": len(invalid_ssns)}
            ))
    
    def _validate_numeric_format(self, field: str):
        """Validate numeric field formats"""
        if field not in self.df.columns:
            return
        
        invalid_numeric = []
        for idx, value in self.df[field].items():
            if pd.isnull(value):
                continue
            
            try:
                float(value)
            except (ValueError, TypeError):
                invalid_numeric.append(idx)
        
        if invalid_numeric:
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.CRITICAL,
                severity=Severity.MEDIUM,
                category=Category.FORMAT_ERROR,
                title=f"Invalid Numeric Format in {field}",
                description=f"{len(invalid_numeric)} records have non-numeric values in {field}.",
                affected_rows=invalid_numeric,
                affected_employees=len(invalid_numeric),
                suggested_action=f"Ensure all {field} values are numeric (remove currency symbols, commas, etc.).",
                auto_fixable=True,
                confidence_score=0.9,
                details={"field_name": field, "invalid_count": len(invalid_numeric)}
            ))
    
    def _validate_cross_field_logic(self):
        """Validate logical relationships between fields"""
        
        # Date logic validation
        if 'DOH' in self.df.columns and 'DOT' in self.df.columns:
            self._validate_date_logic()
        
        # Age validation
        if 'DOB' in self.df.columns:
            self._validate_age_logic()
        
        # Compensation validation
        if 'PriorYearComp' in self.df.columns:
            self._validate_compensation_logic()
    
    def _validate_date_logic(self):
        """Validate date field logic (hire before termination, reasonable ages, etc.)"""
        doh_col = 'DOH'
        dot_col = 'DOT'
        
        if doh_col not in self.df.columns or dot_col not in self.df.columns:
            return
        
        logic_errors = []
        for idx, row in self.df.iterrows():
            doh = row.get(doh_col)
            dot = row.get(dot_col)
            
            if pd.isnull(doh) or pd.isnull(dot):
                continue
            
            try:
                doh_date = pd.to_datetime(doh)
                dot_date = pd.to_datetime(dot)
                
                if dot_date <= doh_date:
                    logic_errors.append(idx)
            except:
                continue
        
        if logic_errors:
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.CRITICAL,
                severity=Severity.HIGH,
                category=Category.LOGIC_ERROR,
                title="Termination Date Before Hire Date",
                description=f"{len(logic_errors)} employees have termination dates on or before their hire dates.",
                affected_rows=logic_errors,
                affected_employees=len(logic_errors),
                suggested_action="Review and correct date entries. Termination date must be after hire date.",
                auto_fixable=False,
                confidence_score=1.0,
                details={"check_type": "date_sequence", "error_count": len(logic_errors)}
            ))
    
    def _validate_age_logic(self):
        """Validate employee ages are reasonable"""
        if 'DOB' not in self.df.columns:
            return
        
        current_year = datetime.now().year
        unreasonable_ages = []
        
        for idx, dob in self.df['DOB'].items():
            if pd.isnull(dob):
                continue
            
            try:
                birth_date = pd.to_datetime(dob)
                age = current_year - birth_date.year
                
                # Flag ages outside reasonable working range
                if age < 16 or age > 90:
                    unreasonable_ages.append(idx)
            except:
                continue
        
        if unreasonable_ages:
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.WARNING,
                severity=Severity.MEDIUM,
                category=Category.ANOMALY,
                title="Unreasonable Employee Ages",
                description=f"{len(unreasonable_ages)} employees have ages outside the typical working range (16-90 years).",
                affected_rows=unreasonable_ages,
                affected_employees=len(unreasonable_ages),
                suggested_action="Verify birth dates for employees with unusual ages.",
                auto_fixable=False,
                confidence_score=0.8,
                details={"age_range": "16-90", "outlier_count": len(unreasonable_ages)}
            ))
    
    def _validate_compensation_logic(self):
        """Validate compensation amounts are reasonable"""
        if 'PriorYearComp' not in self.df.columns:
            return
        
        comp_col = 'PriorYearComp'
        unusual_comp = []
        
        for idx, comp in self.df[comp_col].items():
            if pd.isnull(comp):
                continue
            
            try:
                comp_value = float(comp)
                
                # Flag extremely low or high compensation
                if comp_value < 1000 or comp_value > 10000000:  # $1K to $10M range
                    unusual_comp.append(idx)
            except:
                continue
        
        if unusual_comp:
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.WARNING,
                severity=Severity.MEDIUM,
                category=Category.ANOMALY,
                title="Unusual Compensation Amounts",
                description=f"{len(unusual_comp)} employees have compensation outside typical range ($1,000 - $10,000,000).",
                affected_rows=unusual_comp,
                affected_employees=len(unusual_comp),
                suggested_action="Verify compensation amounts for employees with unusual values.",
                auto_fixable=False,
                confidence_score=0.7,
                details={"comp_range": "$1,000 - $10,000,000", "outlier_count": len(unusual_comp)}
            ))
    
    def _detect_compensation_anomalies(self):
        """Detect unusual compensation patterns and spikes"""
        if 'PriorYearComp' not in self.df.columns:
            return
        
        # Convert to numeric, handling any formatting issues
        comp_series = pd.to_numeric(self.df['PriorYearComp'], errors='coerce')
        
        # Statistical outlier detection using IQR method
        Q1 = comp_series.quantile(0.25)
        Q3 = comp_series.quantile(0.75)
        IQR = Q3 - Q1
        
        # Define outliers as values beyond 2.5 * IQR from quartiles
        outlier_threshold_low = Q1 - 2.5 * IQR
        outlier_threshold_high = Q3 + 2.5 * IQR
        
        outliers = comp_series[(comp_series < outlier_threshold_low) | (comp_series > outlier_threshold_high)]
        
        if len(outliers) > 0:
            outlier_indices = outliers.index.tolist()
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.WARNING,
                severity=Severity.MEDIUM,
                category=Category.ANOMALY,
                title="Statistical Compensation Outliers",
                description=f"{len(outliers)} employees have compensation significantly different from the group average.",
                affected_rows=outlier_indices,
                affected_employees=len(outlier_indices),
                suggested_action="Review compensation data for potential data entry errors or verify if outliers are legitimate.",
                auto_fixable=False,
                confidence_score=0.6,
                details={
                    "method": "IQR_2.5",
                    "outlier_count": len(outliers),
                    "median_comp": float(comp_series.median()),
                    "outlier_range": f"< ${outlier_threshold_low:,.0f} or > ${outlier_threshold_high:,.0f}"
                }
            ))
        
        # Historical comparison if available
        if self.historical_data is not None and 'PriorYearComp' in self.historical_data.columns:
            self._detect_compensation_changes()
    
    def _detect_compensation_changes(self):
        """Detect significant year-over-year compensation changes"""
        if self.historical_data is None:
            return
        
        # This would require matching employees between datasets
        # Implementation depends on employee identifier strategy
        pass
    
    def _detect_demographic_inconsistencies(self):
        """Detect unusual demographic patterns"""
        
        # Age distribution analysis
        if 'DOB' in self.df.columns:
            self._analyze_age_distribution()
        
        # Gender distribution (if available)
        if 'Gender' in self.df.columns:
            self._analyze_gender_distribution()
    
    def _analyze_age_distribution(self):
        """Analyze age distribution for unusual patterns"""
        if 'DOB' not in self.df.columns:
            return
        
        current_year = datetime.now().year
        ages = []
        
        for dob in self.df['DOB']:
            if pd.isnull(dob):
                continue
            try:
                birth_date = pd.to_datetime(dob)
                age = current_year - birth_date.year
                ages.append(age)
            except:
                continue
        
        if len(ages) < 5:  # Need minimum sample size
            return
        
        ages_series = pd.Series(ages)
        
        # Check for unusual age clustering
        age_counts = ages_series.value_counts()
        most_common_age = age_counts.index[0]
        most_common_count = age_counts.iloc[0]
        
        # Flag if more than 30% of employees have the same age
        if most_common_count / len(ages) > 0.3:
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.INFO,
                severity=Severity.LOW,
                category=Category.ANOMALY,
                title="Unusual Age Clustering",
                description=f"{most_common_count} employees ({most_common_count/len(ages)*100:.1f}%) are age {most_common_age}.",
                affected_rows=[],
                affected_employees=most_common_count,
                suggested_action="Verify birth date data entry. High age clustering may indicate data entry errors.",
                auto_fixable=False,
                confidence_score=0.5,
                details={
                    "most_common_age": most_common_age,
                    "cluster_percentage": most_common_count/len(ages)*100,
                    "total_ages_analyzed": len(ages)
                }
            ))
    
    def _detect_mass_events(self):
        """Detect mass hiring/termination events"""
        
        # Mass terminations
        if 'DOT' in self.df.columns:
            self._detect_mass_terminations()
        
        # Mass hiring
        if 'DOH' in self.df.columns:
            self._detect_mass_hiring()
    
    def _detect_mass_terminations(self):
        """Detect mass termination events"""
        if 'DOT' not in self.df.columns:
            return
        
        # Group by termination date
        term_dates = self.df['DOT'].dropna()
        if len(term_dates) == 0:
            return
        
        date_counts = term_dates.value_counts()
        
        # Flag if more than 10 employees terminated on same date
        mass_term_dates = date_counts[date_counts >= 10]
        
        for date, count in mass_term_dates.items():
            affected_rows = self.df[self.df['DOT'] == date].index.tolist()
            
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.WARNING,
                severity=Severity.MEDIUM,
                category=Category.ANOMALY,
                title="Mass Termination Event",
                description=f"{count} employees terminated on {date}. This may impact coverage testing.",
                affected_rows=affected_rows,
                affected_employees=count,
                suggested_action="Confirm mass termination event and consider impact on 410(b) coverage testing.",
                auto_fixable=False,
                confidence_score=0.8,
                details={
                    "termination_date": str(date),
                    "employee_count": count,
                    "compliance_impact": "410(b) coverage testing"
                }
            ))
    
    def _detect_mass_hiring(self):
        """Detect mass hiring events"""
        if 'DOH' not in self.df.columns:
            return
        
        # Group by hire date
        hire_dates = self.df['DOH'].dropna()
        if len(hire_dates) == 0:
            return
        
        date_counts = hire_dates.value_counts()
        
        # Flag if more than 15 employees hired on same date
        mass_hire_dates = date_counts[date_counts >= 15]
        
        for date, count in mass_hire_dates.items():
            affected_rows = self.df[self.df['DOH'] == date].index.tolist()
            
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.WARNING,
                severity=Severity.LOW,
                category=Category.ANOMALY,
                title="Mass Hiring Event",
                description=f"{count} employees hired on {date}. Verify this is accurate.",
                affected_rows=affected_rows,
                affected_employees=count,
                suggested_action="Confirm mass hiring event details are correct.",
                auto_fixable=False,
                confidence_score=0.7,
                details={
                    "hire_date": str(date),
                    "employee_count": count
                }
            ))
    
    def _detect_statistical_outliers(self):
        """Detect statistical outliers across numeric fields"""
        numeric_fields = ['PriorYearComp', 'EmployeeDeferrals', 'EmployerMatch', 'HoursWorked']
        
        for field in numeric_fields:
            if field not in self.df.columns:
                continue
            
            series = pd.to_numeric(self.df[field], errors='coerce')
            if series.isnull().all():
                continue
            
            # Z-score method for outlier detection
            z_scores = np.abs((series - series.mean()) / series.std())
            outliers = series[z_scores > 3]  # 3 standard deviations
            
            if len(outliers) > 0:
                outlier_indices = outliers.index.tolist()
                self.validation_issues.append(ValidationIssue(
                    issue_type=IssueType.INFO,
                    severity=Severity.LOW,
                    category=Category.ANOMALY,
                    title=f"Statistical Outliers in {field}",
                    description=f"{len(outliers)} values in {field} are more than 3 standard deviations from the mean.",
                    affected_rows=outlier_indices,
                    affected_employees=len(outlier_indices),
                    suggested_action=f"Review {field} values that are significantly different from the group average.",
                    auto_fixable=False,
                    confidence_score=0.4,
                    details={
                        "field": field,
                        "method": "z_score_3_std",
                        "outlier_count": len(outliers),
                        "mean": float(series.mean()),
                        "std": float(series.std())
                    }
                ))
    
    def _detect_pattern_anomalies(self):
        """Detect unusual patterns in data"""
        
        # Identical values pattern
        for col in self.df.columns:
            if col in ['SSN', 'EEID']:  # Skip ID fields
                continue
            
            value_counts = self.df[col].value_counts()
            if len(value_counts) == 0:
                continue
            
            most_common_value = value_counts.index[0]
            most_common_count = value_counts.iloc[0]
            
            # Flag if more than 25% have identical values (excluding nulls)
            non_null_count = self.df[col].notna().sum()
            if non_null_count > 0 and most_common_count / non_null_count > 0.25:
                affected_rows = self.df[self.df[col] == most_common_value].index.tolist()
                
                self.validation_issues.append(ValidationIssue(
                    issue_type=IssueType.INFO,
                    severity=Severity.LOW,
                    category=Category.ANOMALY,
                    title=f"Identical Values Pattern in {col}",
                    description=f"{most_common_count} employees ({most_common_count/non_null_count*100:.1f}%) have identical {col} values: {most_common_value}",
                    affected_rows=affected_rows,
                    affected_employees=most_common_count,
                    suggested_action=f"Verify if identical {col} values are intentional or indicate data entry errors.",
                    auto_fixable=False,
                    confidence_score=0.3,
                    details={
                        "field": col,
                        "identical_value": str(most_common_value),
                        "pattern_percentage": most_common_count/non_null_count*100
                    }
                ))
    
    def _detect_round_number_bias(self):
        """Detect round number bias in compensation fields"""
        comp_fields = ['PriorYearComp', 'EmployeeDeferrals', 'EmployerMatch']
        
        for field in comp_fields:
            if field not in self.df.columns:
                continue
            
            series = pd.to_numeric(self.df[field], errors='coerce').dropna()
            if len(series) == 0:
                continue
            
            # Count values ending in 000
            round_numbers = series[series % 1000 == 0]
            round_percentage = len(round_numbers) / len(series) * 100
            
            # Flag if more than 50% are round numbers
            if round_percentage > 50:
                round_indices = round_numbers.index.tolist()
                
                self.validation_issues.append(ValidationIssue(
                    issue_type=IssueType.INFO,
                    severity=Severity.LOW,
                    category=Category.ANOMALY,
                    title=f"Round Number Bias in {field}",
                    description=f"{round_percentage:.1f}% of {field} values end in 000, which is higher than typical.",
                    affected_rows=round_indices,
                    affected_employees=len(round_indices),
                    suggested_action=f"Verify if round numbers in {field} are accurate or estimated values.",
                    auto_fixable=False,
                    confidence_score=0.3,
                    details={
                        "field": field,
                        "round_percentage": round_percentage,
                        "industry_typical": "< 35%"
                    }
                ))
    
    def _validate_compliance_readiness(self):
        """Check if data is ready for compliance testing"""
        
        # HCE determination readiness
        hce_required = ['SSN', 'PriorYearComp', '%Ownership', 'Officer']
        missing_hce_fields = [field for field in hce_required if field not in self.df.columns]
        
        if missing_hce_fields:
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.WARNING,
                severity=Severity.MEDIUM,
                category=Category.COMPLIANCE_ERROR,
                title="HCE Determination Fields Missing",
                description=f"Missing fields for HCE determination: {', '.join(missing_hce_fields)}",
                affected_rows=[],
                affected_employees=len(self.df),
                suggested_action="Add missing fields or ensure proper column mapping for HCE determination.",
                auto_fixable=False,
                confidence_score=0.9,
                details={
                    "missing_fields": missing_hce_fields,
                    "required_for": "HCE determination",
                    "compliance_test": "ADP/ACP"
                }
            ))
        
        # Eligibility testing readiness
        eligibility_required = ['DOB', 'DOH', 'HoursWorked']
        missing_eligibility_fields = [field for field in eligibility_required if field not in self.df.columns]
        
        if missing_eligibility_fields:
            self.validation_issues.append(ValidationIssue(
                issue_type=IssueType.WARNING,
                severity=Severity.MEDIUM,
                category=Category.COMPLIANCE_ERROR,
                title="Eligibility Testing Fields Missing",
                description=f"Missing fields for eligibility testing: {', '.join(missing_eligibility_fields)}",
                affected_rows=[],
                affected_employees=len(self.df),
                suggested_action="Add missing fields for comprehensive eligibility analysis.",
                auto_fixable=False,
                confidence_score=0.8,
                details={
                    "missing_fields": missing_eligibility_fields,
                    "required_for": "eligibility testing",
                    "compliance_test": "410(b) coverage"
                }
            ))
    
    def _calculate_data_quality_score(self):
        """Calculate overall data quality score (0-100)"""
        score = 100.0
        
        # Deduct points based on issue severity and type
        for issue in self.validation_issues:
            if issue.issue_type == IssueType.CRITICAL:
                if issue.severity == Severity.HIGH:
                    score -= 15
                elif issue.severity == Severity.MEDIUM:
                    score -= 10
                else:
                    score -= 5
            elif issue.issue_type == IssueType.WARNING:
                if issue.severity == Severity.HIGH:
                    score -= 8
                elif issue.severity == Severity.MEDIUM:
                    score -= 5
                else:
                    score -= 2
            elif issue.issue_type == IssueType.INFO:
                score -= 1  # Minor deduction for info issues
        
        # Ensure score doesn't go below 0
        self.data_quality_score = max(0.0, score)
    
    def save_validation_results(self) -> None:
        """Save validation results to database"""
        try:
            # Clear existing results for this file
            self.db.query(ValidationResult).filter(
                ValidationResult.file_upload_id == self.file_upload_id
            ).delete()
            
            # Save new results
            for issue in self.validation_issues:
                validation_result = ValidationResult(
                    file_upload_id=self.file_upload_id,
                    issue_type=issue.issue_type.value,
                    severity=issue.severity.value,
                    category=issue.category.value,
                    title=issue.title,
                    description=issue.description,
                    affected_rows=issue.affected_rows,
                    affected_employees=issue.affected_employees,
                    suggested_action=issue.suggested_action,
                    auto_fixable=issue.auto_fixable,
                    is_resolved=issue.is_resolved,
                    confidence_score=issue.confidence_score,
                    details=issue.details,
                    resolved_at=datetime.now() if issue.is_resolved else None,
                    resolution_notes="Auto-fixed" if issue.is_resolved else None,
                    resolved_by=None  # Set to None since we're not tracking user resolution yet
                )
                self.db.add(validation_result)
            
            # Update file upload with data quality score
            file_upload = self.db.query(FileUpload).filter(
                FileUpload.id == self.file_upload_id
            ).first()
            
            if file_upload:
                # Add data quality score to file metadata if column exists
                # This would require adding a data_quality_score column to FileUpload model
                pass
            
            self.db.commit()
            logger.info(f"Saved {len(self.validation_issues)} validation results for file {self.file_upload_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving validation results: {str(e)}")
            raise
    
    def get_auto_fixable_issues(self) -> List[ValidationIssue]:
        """Get list of issues that can be automatically fixed"""
        return [issue for issue in self.validation_issues if issue.auto_fixable]
    
    def apply_auto_fixes(self, issue_ids: List[str] = None) -> pd.DataFrame:
        """
        Apply automatic fixes to the data
        Returns the corrected DataFrame
        """
        corrected_df = self.df.copy()
        
        auto_fixable = self.get_auto_fixable_issues()
        if issue_ids:
            # Filter to only specified issues
            auto_fixable = [issue for issue in auto_fixable if issue.title in issue_ids]
        
        for issue in auto_fixable:
            if issue.category == Category.FORMAT_ERROR:
                if "Date Format" in issue.title:
                    corrected_df = self._auto_fix_date_format(corrected_df, issue)
                    issue.is_resolved = True
                elif "SSN Format" in issue.title:
                    corrected_df = self._auto_fix_ssn_format(corrected_df, issue)
                    issue.is_resolved = True
                elif "Numeric Format" in issue.title:
                    corrected_df = self._auto_fix_numeric_format(corrected_df, issue)
                    issue.is_resolved = True
        
        # Update the original DataFrame with corrections
        self.df = corrected_df
        
        return corrected_df
    
    def _auto_fix_date_format(self, df: pd.DataFrame, issue: ValidationIssue) -> pd.DataFrame:
        """Auto-fix date format issues"""
        field_name = issue.details.get('field_name')
        if not field_name or field_name not in df.columns:
            return df
        
        for idx in issue.affected_rows:
            try:
                # Try to parse and reformat date
                original_value = df.at[idx, field_name]
                if pd.isnull(original_value):
                    continue
                
                parsed_date = pd.to_datetime(original_value, infer_datetime_format=True)
                df.at[idx, field_name] = parsed_date.strftime('%Y-%m-%d')
                
            except Exception as e:
                logger.warning(f"Could not auto-fix date at row {idx}: {str(e)}")
                continue
        
        return df
    
    def _auto_fix_ssn_format(self, df: pd.DataFrame, issue: ValidationIssue) -> pd.DataFrame:
        """Auto-fix SSN format issues"""
        for idx in issue.affected_rows:
            try:
                original_ssn = str(df.at[idx, 'SSN']).strip()
                # Remove any non-digit characters and reformat
                digits_only = re.sub(r'\D', '', original_ssn)
                
                if len(digits_only) == 9:
                    formatted_ssn = f"{digits_only[:3]}-{digits_only[3:5]}-{digits_only[5:]}"
                    df.at[idx, 'SSN'] = formatted_ssn
                    
            except Exception as e:
                logger.warning(f"Could not auto-fix SSN at row {idx}: {str(e)}")
                continue
        
        return df
    
    def _auto_fix_numeric_format(self, df: pd.DataFrame, issue: ValidationIssue) -> pd.DataFrame:
        """Auto-fix numeric format issues"""
        field_name = issue.details.get('field_name')
        if not field_name or field_name not in df.columns:
            return df
        
        for idx in issue.affected_rows:
            try:
                original_value = str(df.at[idx, field_name]).strip()
                # Remove currency symbols, commas, and other non-numeric characters except decimal point
                cleaned_value = re.sub(r'[^\d.-]', '', original_value)
                
                if cleaned_value:
                    numeric_value = float(cleaned_value)
                    df.at[idx, field_name] = numeric_value
                    
            except Exception as e:
                logger.warning(f"Could not auto-fix numeric value at row {idx}: {str(e)}")
                continue
        
        return df