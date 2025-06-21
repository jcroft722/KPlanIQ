from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DataMapper API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "DataMapper API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 

from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from .models import ComplianceTestRun, ComplianceTestResult
from .compliance import ComplianceEngine

# Add these new endpoints

@app.get("/api/compliance/results")
async def get_compliance_results(db: Session = Depends(get_db)):
    """Get recent compliance test results for dashboard"""
    try:
        # Get recent test runs with file info
        recent_runs = db.query(ComplianceTestRun)\
            .options(joinedload(ComplianceTestRun.file))\
            .order_by(ComplianceTestRun.run_date.desc())\
            .limit(10)\
            .all()
        
        results = []
        for run in recent_runs:
            results.append({
                "id": run.id,
                "file_id": run.file_id,
                "file_name": run.file.original_filename if run.file else "Unknown",
                "run_date": run.run_date.isoformat(),
                "total_tests": run.total_tests,
                "passed_tests": run.passed_tests,
                "failed_tests": run.failed_tests,
                "results": []  # Can include detailed results if needed
            })
        
        return {"recent_results": results}
        
    except Exception as e:
        logger.error(f"Error fetching compliance results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching compliance results: {str(e)}")

@app.get("/api/compliance/history")
async def get_compliance_history(db: Session = Depends(get_db)):
    """Get full compliance test history"""
    try:
        # Get all test runs with detailed results
        test_runs = db.query(ComplianceTestRun)\
            .options(
                joinedload(ComplianceTestRun.file),
                joinedload(ComplianceTestRun.test_results)
            )\
            .order_by(ComplianceTestRun.run_date.desc())\
            .all()
        
        history = []
        for run in test_runs:
            detailed_results = []
            for result in run.test_results:
                detailed_results.append({
                    "id": result.id,
                    "test_id": result.test_id,
                    "test_name": result.test_name,
                    "test_category": result.test_category,
                    "status": result.status,
                    "message": result.message,
                    "affected_employees": result.affected_employees,
                    "details": result.details,
                    "created_at": result.created_at.isoformat()
                })
            
            history.append({
                "id": run.id,
                "file_id": run.file_id,
                "file_name": run.file.original_filename if run.file else "Unknown",
                "run_date": run.run_date.isoformat(),
                "total_tests": run.total_tests,
                "passed_tests": run.passed_tests,
                "failed_tests": run.failed_tests,
                "results": detailed_results
            })
        
        return {"test_runs": history}
        
    except Exception as e:
        logger.error(f"Error fetching compliance history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching compliance history: {str(e)}")

@app.post("/api/files/{file_id}/compliance-test")
async def run_compliance_tests(file_id: int, db: Session = Depends(get_db)):
    """Run compliance tests on uploaded file and store results"""
    try:
        # Get file from database
        file_record = db.query(FileUpload).filter(FileUpload.id == file_id).first()
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Load the data
        file_path = f"uploads/{file_record.filename}"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File data not found")
        
        # Read file based on extension
        file_ext = file_record.filename.split('.')[-1].lower()
        if file_ext == 'csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['xlsx', 'xls']:
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Run compliance tests
        compliance_engine = ComplianceEngine(df)
        test_results = compliance_engine.run_all_tests()
        
        # Create test run record
        test_run = ComplianceTestRun(
            file_id=file_id,
            total_tests=len(test_results),
            passed_tests=len([r for r in test_results if r.passed]),
            failed_tests=len([r for r in test_results if not r.passed])
        )
        db.add(test_run)
        db.flush()  # Get the ID
        
        # Store individual test results
        stored_results = []
        for result in test_results:
            test_result = ComplianceTestResult(
                test_run_id=test_run.id,
                test_id=result.test_id,
                test_name=result.test_id.replace('_', ' ').title(),  # Convert to readable name
                test_category=get_test_category(result.test_id),
                status='passed' if result.passed else 'failed',
                message=result.message,
                affected_employees=result.affected_employees,
                details=result.details
            )
            db.add(test_result)
            
            stored_results.append({
                "test_id": result.test_id,
                "passed": result.passed,
                "message": result.message,
                "details": result.details,
                "affected_employees": result.affected_employees
            })
        
        db.commit()
        
        return {
            "test_run_id": test_run.id,
            "results": stored_results,
            "summary": {
                "total_tests": len(test_results),
                "passed_tests": len([r for r in test_results if r.passed]),
                "failed_tests": len([r for r in test_results if not r.passed])
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error running compliance tests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running compliance tests: {str(e)}")

def get_test_category(test_id: str) -> str:
    """Map test IDs to categories"""
    category_map = {
        'min_age': 'eligibility',
        'service_requirement': 'eligibility',
        'annual_compensation_limit': 'limits',
        'deferral_limit': 'limits',
        'catch_up_limit': 'limits',
        'acp_test': 'discrimination',
        'adp_test': 'discrimination',
        'top_heavy': 'discrimination',
        'coverage_ratio': 'coverage',
        'minimum_participation': 'coverage'
    }
    return category_map.get(test_id, 'other')

@app.get("/api/uploads")
async def get_uploads(db: Session = Depends(get_db)):
    """Get all uploaded files"""
    try:
        files = db.query(FileUpload).order_by(FileUpload.created_at.desc()).all()
        
        file_list = []
        for file in files:
            file_list.append({
                "id": file.id,
                "original_filename": file.original_filename,
                "filename": file.filename,
                "size": file.size,
                "rows": file.rows,
                "columns": file.columns,
                "status": file.status,
                "created_at": file.created_at.isoformat()
            })
        
        return {"files": file_list}
        
    except Exception as e:
        logger.error(f"Error fetching uploads: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching uploads: {str(e)}")