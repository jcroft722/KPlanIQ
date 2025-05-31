from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
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
    ColumnMapping
)

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
            "uploaded_at": datetime.now().isoformat(),
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
                "uploaded_at": db_file.uploaded_at.isoformat(),
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
            "uploaded_at": db_file.uploaded_at.isoformat(),
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