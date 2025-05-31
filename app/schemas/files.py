from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime

class FileUploadBase(BaseModel):
    filename: str
    original_filename: str
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    headers: Optional[List[str]] = None
    status: str = "uploaded"

class FileUploadCreate(FileUploadBase):
    pass

class FileUpload(FileUploadBase):
    id: int
    created_at: datetime
    uploaded_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ComplianceResult(BaseModel):
    id: int
    test_name: str
    status: str
    run_date: datetime
    details: Optional[Union[str, dict]] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 