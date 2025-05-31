from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json
import os
from pathlib import Path

from app.core.database import get_db
from app.models.models import FileUpload, ComplianceTest
from app.schemas.files import FileUpload as FileUploadSchema
from app.schemas.files import ComplianceResult, FileUploadCreate

router = APIRouter()

@router.get("/uploads", response_model=List[FileUploadSchema])
def get_uploads(db: Session = Depends(get_db)):
    return db.query(FileUpload).all()

@router.post("/upload", response_model=FileUploadSchema)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / unique_filename
    
    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create file upload record
    file_upload = FileUpload(
        filename=unique_filename,
        original_filename=file.filename,
        file_size=len(content),
        file_path=str(file_path),
        mime_type=file.content_type,
        status="uploaded",
        created_at=datetime.utcnow(),
        uploaded_at=datetime.utcnow(),
        row_count=100,  # Replace with actual row count
        column_count=15,  # Replace with actual column count
        headers=json.dumps(['SSN', 'EEID', 'FirstName', 'LastName', 'DOB', 'DOH', 'DOT', 
                          'HoursWorked', '%Ownership', 'Officer', 'PiorYearComp', 
                          'EmployeeDeferrals', 'EmployerMatch', 'EmployerProfitSharing', 
                          'EmployerSHContribuion'])
    )
    
    db.add(file_upload)
    db.commit()
    db.refresh(file_upload)
    return file_upload

@router.post("/process/{file_id}", response_model=FileUploadSchema)
async def process_file(file_id: int, db: Session = Depends(get_db)):
    # Get the file upload record
    file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
    if not file_upload:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Update the status to processed
        file_upload.status = "processed"
        db.commit()
        db.refresh(file_upload)
        return file_upload
    except Exception as e:
        file_upload.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compliance-results", response_model=List[ComplianceResult])
def get_compliance_results(db: Session = Depends(get_db)):
    results = db.query(ComplianceTest).all()
    if not results:
        return []  # Return empty list instead of 404 to avoid frontend errors
    return results 