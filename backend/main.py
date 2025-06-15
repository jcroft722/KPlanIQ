print("Starting main.py...")
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import os
from datetime import datetime
import pandas as pd
import io
import logging
from sqlalchemy.orm import Session
from app.core.database import get_db, Base, engine
from app.models.models import (
    FileUpload,
    EmployeeData,
    RawEmployeeData,
    ColumnMapping,
    ValidationResult,
    DataQualityScore,
    ValidationRun
)
from app.services.validation_engine import DataValidationEngine

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Standard column names for 401k data
STANDARD_COLUMNS = {
    'ssn': 'SSN',
    'eeid': 'EEID',
    'first_name': 'FirstName',
    'last_name': 'LastName',
    'dob': 'DOB',
    'doh': 'DOH',
    'dot': 'DOT',
    'hours_worked': 'HoursWorked',
    'ownership_percentage': '%Ownership',
    'is_officer': 'Officer',
    'prior_year_comp': 'PiorYearComp',
    'employee_deferrals': 'EmployeeDeferrals',
    'employer_match': 'EmployerMatch',
    'employer_profit_sharing': 'EmployerProfitSharing',
    'employer_sh_contribution': 'EmployerSHContribuion'
}

# Common variations for auto-mapping
COLUMN_VARIATIONS = {
    'SSN': ['ssn', 'social_security', 'social security number', 'socialsecurity'],
    'EEID': ['employeeid', 'emp_id', 'employee_id', 'empid'],
    'FirstName': ['first', 'firstname', 'first_name', 'fname'],
    'LastName': ['last', 'lastname', 'last_name', 'lname'],
    'DOB': ['birthdate', 'birth_date', 'dateofbirth', 'date_of_birth'],
    'DOH': ['hiredate', 'hire_date', 'dateofhire', 'date_of_hire'],
    'DOT': ['termdate', 'term_date', 'dateofterm', 'date_of_termination'],
    'HoursWorked': ['hours', 'work_hours', 'total_hours'],
    '%Ownership': ['own', 'ownership', 'ownership_pct', 'owner_percent'],
    'Officer': ['is_officer', 'officer_status', 'isofficer'],
    'PiorYearComp': ['prior_comp', 'prior_year', 'previous_comp'],
    'EmployeeDeferrals': ['deferrals', 'emp_deferrals', 'employee_def'],
    'EmployerMatch': ['match', 'employer_matching', 'company_match'],
    'EmployerProfitSharing': ['profit_sharing', 'profitshare', 'profit_share'],
    'EmployerSHContribuion': ['sh_contribution', 'safe_harbor', 'sh_contrib']
}

def suggest_column_mappings(source_columns: List[str]) -> Dict[str, dict]:
    """Suggest column mappings using multiple matching strategies."""
    mappings = {}
    
    for source_col in source_columns:
        source_lower = source_col.lower().replace(' ', '_')
        mapping = {
            'source_column': source_col,
            'target_column': None,
            'mapping_type': None,
            'confidence_score': 0.0
        }
        
        # Try exact match
        if source_col in STANDARD_COLUMNS.values():
            mapping['target_column'] = source_col
            mapping['mapping_type'] = 'auto_exact'
            mapping['confidence_score'] = 1.0
        
        # Try variation match
        if not mapping['target_column']:
            for target, variations in COLUMN_VARIATIONS.items():
                if source_lower in [v.lower() for v in variations]:
                    mapping['target_column'] = target
                    mapping['mapping_type'] = 'auto_fuzzy'
                    mapping['confidence_score'] = 0.8
                    break
        
        # Try partial match (if no better match found)
        if not mapping['target_column']:
            for target, variations in COLUMN_VARIATIONS.items():
                if any(v.lower() in source_lower or source_lower in v.lower() for v in variations):
                    mapping['target_column'] = target
                    mapping['mapping_type'] = 'auto_fuzzy'
                    mapping['confidence_score'] = 0.6
                    break
        
        mappings[source_col] = mapping
    
    return mappings

def process_file(file_content: bytes, filename: str) -> tuple[pd.DataFrame, dict]:
    """Process the uploaded file and return DataFrame and metadata."""
    try:
        logger.debug(f"Processing file: {filename}")
        file_buffer = io.BytesIO(file_content)
        
        if filename.lower().endswith('.csv'):
            logger.debug("Reading CSV file")
            df = pd.read_csv(file_buffer)
        elif filename.lower().endswith(('.xlsx', '.xls')):
            logger.debug("Reading Excel file")
            df = pd.read_excel(file_buffer)
        else:
            raise ValueError("Unsupported file format")

        logger.debug(f"File read successfully. Shape: {df.shape}")
        logger.debug(f"Columns: {df.columns.tolist()}")

        # Get suggested mappings
        suggested_mappings = suggest_column_mappings(df.columns.tolist())
        logger.debug(f"Suggested mappings: {suggested_mappings}")

        metadata = {
            "rows": len(df),
            "columns": len(df.columns),
            "headers": df.columns.tolist(),
            "suggested_mappings": suggested_mappings
        }
        
        logger.debug(f"Extracted metadata: {metadata}")
        return df, metadata
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise ValueError(f"Error processing file: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    try:
        logger.debug(f"Received file upload: {file.filename}")
        content = await file.read()
        
        # Process file and get metadata
        df, metadata = process_file(content, file.filename)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save original file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create database record for file upload
        db_file = FileUpload(
            filename=filename,
            original_filename=file.filename,
            file_size=len(content),
            file_path=file_path,
            mime_type=file.content_type,
            row_count=metadata["rows"],
            column_count=metadata["columns"],
            headers=metadata["headers"],
            status="uploaded"
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        logger.debug(f"Created database record for file: {db_file.id}")

        # Store raw data
        logger.debug("Storing raw data records...")
        for _, row in df.iterrows():
            # Convert any non-string values to strings to ensure JSON serialization
            row_dict = {}
            for col, val in row.items():
                if pd.isna(val):
                    row_dict[col] = None
                else:
                    row_dict[col] = str(val) if not isinstance(val, (int, float, bool)) else val
            
            raw_record = RawEmployeeData(
                file_upload_id=db_file.id,
                row_data=row_dict
            )
            db.add(raw_record)
        
        # Store suggested column mappings
        logger.debug("Storing suggested column mappings...")
        for source_col, mapping in metadata["suggested_mappings"].items():
            if mapping.get("target_column"):
                column_mapping = ColumnMapping(
                    file_upload_id=db_file.id,
                    source_column=source_col,
                    target_column=mapping["target_column"],
                    mapping_type=mapping.get("mapping_type", "auto_exact"),
                    confidence_score=mapping.get("confidence_score", 1.0)
                )
                db.add(column_mapping)
        
        db.commit()
        logger.debug("Raw data and mappings stored successfully")
        
        response_data = {
            "id": db_file.id,
            "filename": filename,
            "original_filename": file.filename,
            "file_size": len(content),
            "file_path": file_path,
            "mime_type": file.content_type,
            "status": "uploaded",
            "uploaded_at": datetime.now().isoformat() if datetime.now() else None,
            "rows": metadata["rows"],
            "columns": metadata["columns"],
            "headers": metadata["headers"],
            "suggested_mappings": metadata["suggested_mappings"]
        }
        logger.debug(f"Sending response: {response_data}")
        return response_data
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/uploads")
async def list_uploads(db: Session = Depends(get_db)):
    try:
        db_files = db.query(FileUpload).all()
        files = []
        
        for db_file in db_files:
            files.append({
                "id": db_file.id,
                "filename": db_file.filename,
                "original_filename": db_file.original_filename,
                "file_size": db_file.file_size,
                "file_path": db_file.file_path,
                "mime_type": db_file.mime_type,
                "status": db_file.status,
                "uploaded_at": db_file.uploaded_at.isoformat() if db_file.uploaded_at else None,
                "rows": db_file.row_count,
                "columns": db_file.column_count,
                "headers": db_file.headers
            })
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/uploads/{file_id}")
async def get_upload_details(file_id: int, db: Session = Depends(get_db)):
    try:
        db_file = db.query(FileUpload).filter(FileUpload.id == file_id).first()
        if not db_file:
            raise HTTPException(status_code=404, detail="File not found")
            
        return {
            "id": db_file.id,
            "filename": db_file.filename,
            "original_filename": db_file.original_filename,
            "file_size": db_file.file_size,
            "file_path": db_file.file_path,
            "mime_type": db_file.mime_type,
            "status": db_file.status,
            "uploaded_at": db_file.uploaded_at.isoformat() if db_file.uploaded_at else None,
            "rows": db_file.row_count,
            "columns": db_file.column_count,
            "headers": db_file.headers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{file_id}/mappings")
async def get_column_mappings(file_id: int, db: Session = Depends(get_db)):
    """Get current column mappings and suggestions for a file."""
    try:
        # Get file upload record
        file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        # Get existing mappings
        mappings = db.query(ColumnMapping).filter(ColumnMapping.file_upload_id == file_id).all()
        
        # Convert to dictionary for easy lookup
        current_mappings = {}
        for mapping in mappings:
            current_mappings[mapping.source_column] = {
                "id": mapping.id,
                "source_column": mapping.source_column,
                "target_column": mapping.target_column,
                "mapping_type": mapping.mapping_type,
                "confidence_score": float(mapping.confidence_score) if mapping.confidence_score else None
            }
            
        # Get all available target columns from our schema
        available_target_columns = {
            col: {
                "name": display_name,
                "variations": COLUMN_VARIATIONS.get(display_name, [])
            }
            for col, display_name in STANDARD_COLUMNS.items()
        }
        
        return {
            "file_id": file_id,
            "original_filename": file_upload.original_filename,
            "source_columns": file_upload.headers,
            "current_mappings": current_mappings,
            "available_target_columns": available_target_columns,
            "unmapped_columns": [
                col for col in file_upload.headers 
                if col not in current_mappings or not current_mappings[col]["target_column"]
            ]
        }
    except Exception as e:
        logger.error(f"Error getting mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/files/{file_id}/mappings")
async def update_column_mappings(
    file_id: int,
    mappings: Dict[str, str],  # source_column -> target_column
    db: Session = Depends(get_db)
):
    """Update column mappings for a file."""
    try:
        # Get file upload record
        file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
            
        # Validate target columns
        invalid_targets = [target for target in mappings.values() 
                         if target and target not in STANDARD_COLUMNS.values()]
        if invalid_targets:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid target columns: {', '.join(invalid_targets)}"
            )
            
        # Update mappings
        for source_col, target_col in mappings.items():
            # Find existing mapping
            mapping = db.query(ColumnMapping).filter(
                ColumnMapping.file_upload_id == file_id,
                ColumnMapping.source_column == source_col
            ).first()
            
            if mapping:
                # Update existing mapping
                mapping.target_column = target_col
                mapping.mapping_type = "manual"
                mapping.confidence_score = 1.0
            else:
                # Create new mapping
                mapping = ColumnMapping(
                    file_upload_id=file_id,
                    source_column=source_col,
                    target_column=target_col,
                    mapping_type="manual",
                    confidence_score=1.0
                )
                db.add(mapping)
        
        db.commit()
        
        # Return updated mappings
        return await get_column_mappings(file_id, db)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating mappings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/{file_id}/process")
async def process_file_endpoint(file_id: int, db: Session = Depends(get_db)):
    # Get the file upload record
    file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
    if not file_upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Get the raw data records
        raw_records = db.query(RawEmployeeData).filter(RawEmployeeData.file_upload_id == file_id).all()
        
        # Get column mappings
        column_mappings = db.query(ColumnMapping).filter(ColumnMapping.file_upload_id == file_id).all()
        mapping_dict = {m.source_column: m.target_column for m in column_mappings}
        
        # Process each raw record and create EmployeeData records
        for raw_record in raw_records:
            row_data = raw_record.row_data
            
            # Map the data according to column mappings
            mapped_data = {}
            for source_col, value in row_data.items():
                if source_col in mapping_dict:
                    target_col = mapping_dict[source_col]
                    mapped_data[target_col] = value
            
            # Create EmployeeData record
            employee_record = EmployeeData(
                file_upload_id=file_id,
                ssn=mapped_data.get('SSN'),
                eeid=mapped_data.get('EEID'),
                first_name=mapped_data.get('FirstName'),
                last_name=mapped_data.get('LastName'),
                dob=datetime.strptime(mapped_data.get('DOB', ''), '%Y-%m-%d') if mapped_data.get('DOB') else None,
                doh=datetime.strptime(mapped_data.get('DOH', ''), '%Y-%m-%d') if mapped_data.get('DOH') else None,
                dot=datetime.strptime(mapped_data.get('DOT', ''), '%Y-%m-%d') if mapped_data.get('DOT') else None,
                hours_worked=float(mapped_data.get('HoursWorked', 0)),
                ownership_percentage=float(mapped_data.get('%Ownership', 0)),
                is_officer=bool(mapped_data.get('Officer', False)),
                prior_year_comp=float(mapped_data.get('PriorYearComp', 0)),
                employee_deferrals=float(mapped_data.get('EmployeeDeferrals', 0)),
                employer_match=float(mapped_data.get('EmployerMatch', 0)),
                employer_profit_sharing=float(mapped_data.get('EmployerProfitSharing', 0)),
                employer_sh_contribution=float(mapped_data.get('EmployerSHContribution', 0))
            )
            
            db.add(employee_record)
            
            # Link the raw record to the mapped record
            raw_record.mapped_record = employee_record
        
        # Update the status to processed
        file_upload.status = "processed"
        db.commit()
        db.refresh(file_upload)
        
        # Return the updated file record
        return {
            "id": file_upload.id,
            "filename": file_upload.filename,
            "original_filename": file_upload.original_filename,
            "status": file_upload.status,
            "uploaded_at": file_upload.created_at,
            "rows": file_upload.row_count,
            "columns": file_upload.column_count,
            "headers": file_upload.headers
        }
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        file_upload.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/{file_id}/validate")
async def run_data_validation(file_id: int, db: Session = Depends(get_db)):
    """Run comprehensive data validation on uploaded file"""
    try:
        # Get file upload record
        file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # CREATE VALIDATION RUN RECORD
        validation_run = ValidationRun(
            file_upload_id=file_id,
            status="running",
            validation_config={"version": "1.0", "checks": "comprehensive"}
        )
        db.add(validation_run)
        db.commit()
        db.refresh(validation_run)
        
        try:
            # Load the data
            if not os.path.exists(file_upload.file_path):
                raise HTTPException(status_code=404, detail=f"File not found at path: {file_upload.file_path}")
                
            if file_upload.filename.endswith('.csv'):
                df = pd.read_csv(file_upload.file_path)
            else:
                df = pd.read_excel(file_upload.file_path)
            
            # Run validation
            start_time = datetime.now()
            validation_engine = DataValidationEngine(df, file_id, db)
            issues, quality_score = validation_engine.run_comprehensive_validation()
            
            # Save validation results
            validation_engine.save_validation_results()
            
            # UPDATE VALIDATION RUN RECORD
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            validation_run.status = "completed"
            validation_run.completed_at = end_time
            validation_run.processing_time_seconds = processing_time
            validation_run.total_issues_found = len(issues)
            validation_run.data_quality_score = quality_score
            validation_run.can_proceed_to_compliance = len([i for i in issues if i.issue_type.value == "critical"]) == 0
            
            db.commit()
            
            return {
                "validation_run_id": validation_run.id,
                "status": validation_run.status,
                "issues_found": len(issues),
                "data_quality_score": quality_score,
                "can_proceed_to_compliance": validation_run.can_proceed_to_compliance,
                "processing_time": processing_time
            }
            
        except Exception as e:
            # UPDATE VALIDATION RUN WITH ERROR
            validation_run.status = "failed"
            validation_run.error_message = str(e)
            validation_run.completed_at = datetime.now()
            db.commit()
            
            logger.error(f"Error in validation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error running validation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{file_id}/validation-results")
async def get_validation_results(file_id: int, db: Session = Depends(get_db)):
    """Get validation results for a file"""
    try:
        # Get file info
        file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get validation results
        validation_results = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_id
        ).order_by(ValidationResult.created_at.desc()).all()
        
        # Get data quality score
        quality_score = db.query(DataQualityScore).filter(
            DataQualityScore.file_upload_id == file_id
        ).first()
        
        # Format response - with careful null checks for all datetime fields
        issues = []
        for result in validation_results:
            # Safely handle any potentially None values
            created_at = None
            if result.created_at:
                try:
                    created_at = result.created_at.isoformat()
                except AttributeError:
                    created_at = None
            
            # Build result dictionary with null checks for all fields
            issue_dict = {
                "id": result.id,
                "issue_type": result.issue_type,
                "severity": result.severity,
                "category": result.category,
                "title": result.title,
                "description": result.description,
                "affected_rows": result.affected_rows or [],
                "affected_employees": result.affected_employees,
                "suggested_action": result.suggested_action,
                "auto_fixable": result.auto_fixable,
                "is_resolved": result.is_resolved,
                "confidence_score": float(result.confidence_score) if result.confidence_score else 0.0,
                "details": result.details or {},
                "created_at": created_at
            }
            issues.append(issue_dict)
        
        # Safely create the quality score section
        quality_score_data = None
        if quality_score:
            # Apply null checks to all datetime fields
            updated_at = None
            if hasattr(quality_score, 'updated_at') and quality_score.updated_at:
                try:
                    updated_at = quality_score.updated_at.isoformat()
                except AttributeError:
                    updated_at = None
            
            quality_score_data = {
                "overall": float(quality_score.overall_score) if quality_score.overall_score else 0.0,
                "completeness": float(quality_score.completeness_score) if quality_score.completeness_score else 0.0,
                "consistency": float(quality_score.consistency_score) if quality_score.consistency_score else 0.0,
                "accuracy": float(quality_score.accuracy_score) if quality_score.accuracy_score else 0.0,
                "critical_issues": quality_score.critical_issues if hasattr(quality_score, 'critical_issues') else 0,
                "warning_issues": quality_score.warning_issues if hasattr(quality_score, 'warning_issues') else 0,
                "anomaly_issues": quality_score.anomaly_issues if hasattr(quality_score, 'anomaly_issues') else 0,
                "last_updated": updated_at
            }
        
        return {
            "file_id": file_id,
            "file_name": file_upload.original_filename,
            "issues": issues,
            "file_stats": {
                "rows": file_upload.row_count,
                "columns": file_upload.column_count
            },
            "quality_score": quality_score_data
        }
        
    except Exception as e:
        logger.error(f"Error getting validation results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/{file_id}/auto-fix")
async def auto_fix_issues(file_id: int, db: Session = Depends(get_db)):
    """Apply automatic fixes to validation issues"""
    try:
        # Get file upload record
        file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Load the data
        if not os.path.exists(file_upload.file_path):
            raise HTTPException(status_code=404, detail=f"File not found at path: {file_upload.file_path}")
            
        if file_upload.filename.endswith('.csv'):
            df = pd.read_csv(file_upload.file_path)
        else:
            df = pd.read_excel(file_upload.file_path)
        
        # Run validation and apply fixes
        validation_engine = DataValidationEngine(df, file_id, db)
        issues, quality_score = validation_engine.run_comprehensive_validation()
        
        # Apply auto-fixes
        corrected_df = validation_engine.apply_auto_fixes()
        
        # Save corrected data back to the original file
        if file_upload.filename.endswith('.csv'):
            corrected_df.to_csv(file_upload.file_path, index=False)
        else:
            corrected_df.to_excel(file_upload.file_path, index=False)
        
        # Update validation results
        validation_engine.save_validation_results()
        
        # Mark auto-fixed issues as resolved
        for issue in issues:
            if issue.auto_fixable:
                db_issue = db.query(ValidationResult).filter(
                    ValidationResult.file_upload_id == file_id,
                    ValidationResult.title == issue.title
                ).first()
                if db_issue:
                    db_issue.is_resolved = True
                    db.commit()
        
        return {
            "message": "Auto-fixes applied successfully",
            "issues_fixed": len([i for i in issues if i.auto_fixable]),
            "quality_score": quality_score
        }
        
    except Exception as e:
        logger.error(f"Error in auto-fix: {str(e)}")
        # Ensure we rollback any failed transaction
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{file_id}/data-quality-score")
async def get_data_quality_score(file_id: int, db: Session = Depends(get_db)):
    """Get data quality score for a file"""
    try:
        quality_score = db.query(DataQualityScore).filter(
            DataQualityScore.file_upload_id == file_id
        ).first()
        
        if not quality_score:
            return {"message": "No quality score available. Run validation first."}
        
        return {
            "file_id": file_id,
            "overall": float(quality_score.overall_score),
            "completeness": float(quality_score.completeness_score),
            "consistency": float(quality_score.consistency_score),
            "accuracy": float(quality_score.accuracy_score),
            "anomaly_count": quality_score.anomaly_issues,
            "critical_issues": quality_score.critical_issues,
            "warning_issues": quality_score.warning_issues,
            "total_issues": quality_score.total_issues,
            "auto_fixable": quality_score.auto_fixable_issues,
            "last_updated": quality_score.updated_at.isoformat() if quality_score.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"Error getting quality score: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/{file_id}/quality-score")
async def get_quality_score(file_id: int, db: Session = Depends(get_db)):
    """Get the data quality score for a file"""
    try:
        # Get the latest validation run for this file
        validation_run = db.query(ValidationRun).filter(
            ValidationRun.file_upload_id == file_id,
            ValidationRun.status == "completed"
        ).order_by(ValidationRun.completed_at.desc()).first()
        
        if not validation_run:
            raise HTTPException(status_code=404, detail="No completed validation run found for this file")
        
        return {
            "file_id": file_id,
            "quality_score": validation_run.data_quality_score,
            "validation_run_id": validation_run.id,
            "completed_at": validation_run.completed_at
        }
        
    except Exception as e:
        logger.error(f"Error getting quality score: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compliance/history")
async def get_compliance_history(db: Session = Depends(get_db)):
    """Get compliance history for all files"""
    try:
        # Get all completed validation runs with compliance status
        validation_runs = db.query(ValidationRun).filter(
            ValidationRun.status == "completed"
        ).order_by(ValidationRun.completed_at.desc()).all()
        
        history = []
        for run in validation_runs:
            file_upload = db.query(FileUpload).filter(FileUpload.id == run.file_upload_id).first()
            if file_upload:
                history.append({
                    "file_id": file_upload.id,
                    "filename": file_upload.filename,
                    "validation_run_id": run.id,
                    "quality_score": run.data_quality_score,
                    "can_proceed_to_compliance": run.can_proceed_to_compliance,
                    "completed_at": run.completed_at,
                    "total_issues_found": run.total_issues_found
                })
        
        return {
            "history": history,
            "total_files": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))