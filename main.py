from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import os
from datetime import datetime
import pandas as pd
import io
import logging
from sqlalchemy.orm import Session
from app.core.database import get_db, Base, engine, recreate_tables
from app.models.models import (
    FileUpload as DBFileUpload,
    EmployeeData,
    RawEmployeeData,
    ColumnMapping
)
from app.routers import files

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Recreate database tables
logger.info("Recreating database tables...")
recreate_tables()
logger.info("Database tables recreated successfully")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Include routers
app.include_router(files.router, prefix="/api/files", tags=["files"])

@app.get("/")
def read_root():
    return {"message": "Welcome to KPlan API"} 