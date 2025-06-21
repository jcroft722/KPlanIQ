# fix_issues_routes.py - FastAPI routes for Fix Issues functionality

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import logging

from ..core.database import get_db
from ..models.models import FileUpload, ValidationResult, DataQualityScore, User
from ..services.validation_engine import DataValidationEngine
from ..services.fix_engine import IssueFixEngine

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request/response
class FixRequest(BaseModel):
    action_type: str  # 'auto_fix', 'manual_entry', 'exclude', 'accept', 'generate_test'
    fix_data: Optional[Dict[str, Any]] = None

class BulkFixRequest(BaseModel):
    issue_ids: List[int]

class StatusUpdateRequest(BaseModel):
    status: str  # 'accepted', 'rejected', 'excluded'

class FixValidationRequest(BaseModel):
    fix_data: Dict[str, Any]

# Apply fix to specific issue
@router.post("/api/files/{file_id}/issues/{issue_id}/fix")
async def apply_issue_fix(
    file_id: int,
    issue_id: int,
    fix_request: FixRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Apply a fix to a specific validation issue."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_upload_id == file_id
        ).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Initialize fix engine
        fix_engine = IssueFixEngine(db, file_upload)
        
        # Apply the fix based on action type
        fix_result = await fix_engine.apply_fix(
            issue, 
            fix_request.action_type, 
            fix_request.fix_data
        )
        
        # Update issue status
        issue.is_resolved = True
        issue.resolution_method = fix_request.action_type
        issue.resolution_data = json.dumps(fix_request.fix_data) if fix_request.fix_data else None
        
        db.commit()
        
        # Recalculate data quality score in background
        background_tasks.add_task(recalculate_quality_score, file_id, db)
        
        return {
            "success": True,
            "message": "Fix applied successfully",
            "fix_result": fix_result
        }
        
    except Exception as e:
        logger.error(f"Error applying fix to issue {issue_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Apply bulk fixes
@router.post("/api/files/{file_id}/issues/bulk-fix")
async def apply_bulk_fixes(
    file_id: int,
    bulk_request: BulkFixRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Apply auto-fixes to multiple issues at once."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issues
        issues = db.query(ValidationResult).filter(
            ValidationResult.id.in_(bulk_request.issue_ids),
            ValidationResult.file_upload_id == file_id,
            ValidationResult.auto_fixable == True,
            ValidationResult.is_resolved == False
        ).all()
        
        if not issues:
            raise HTTPException(status_code=404, detail="No auto-fixable issues found")
        
        # Initialize fix engine
        fix_engine = IssueFixEngine(db, file_upload)
        
        # Apply fixes to all issues
        fix_results = []
        for issue in issues:
            try:
                fix_result = await fix_engine.apply_fix(issue, 'auto_fix', None)
                issue.is_resolved = True
                issue.resolution_method = 'auto_fix'
                fix_results.append({
                    "issue_id": issue.id,
                    "success": True,
                    "result": fix_result
                })
            except Exception as e:
                logger.error(f"Error applying bulk fix to issue {issue.id}: {str(e)}")
                fix_results.append({
                    "issue_id": issue.id,
                    "success": False,
                    "error": str(e)
                })
        
        db.commit()
        
        # Recalculate data quality score in background
        background_tasks.add_task(recalculate_quality_score, file_id, db)
        
        successful_fixes = len([r for r in fix_results if r["success"]])
        
        return {
            "success": True,
            "message": f"Applied {successful_fixes} of {len(bulk_request.issue_ids)} fixes",
            "results": fix_results
        }
        
    except Exception as e:
        logger.error(f"Error applying bulk fixes: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Update issue status
@router.patch("/api/files/{file_id}/issues/{issue_id}/status")
async def update_issue_status(
    file_id: int,
    issue_id: int,
    status_request: StatusUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update the status of a validation issue."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_upload_id == file_id
        ).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Update status
        if status_request.status == 'accepted':
            issue.is_resolved = True
            issue.resolution_method = 'accepted'
        elif status_request.status == 'excluded':
            issue.is_resolved = True
            issue.resolution_method = 'excluded'
        elif status_request.status == 'rejected':
            issue.is_resolved = False
            issue.resolution_method = None
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Issue status updated to {status_request.status}"
        }
        
    except Exception as e:
        logger.error(f"Error updating issue status: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Get fix suggestions for an issue
@router.get("/api/files/{file_id}/issues/{issue_id}/suggestions")
async def get_fix_suggestions(
    file_id: int,
    issue_id: int,
    db: Session = Depends(get_db)
):
    """Get suggested fixes for a validation issue."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_upload_id == file_id
        ).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Initialize fix engine
        fix_engine = IssueFixEngine(db, file_upload)
        
        # Get suggestions
        suggestions = await fix_engine.get_fix_suggestions(issue)
        
        return {
            "issue_id": issue_id,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error getting fix suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Preview auto-fix changes
@router.get("/api/files/{file_id}/issues/{issue_id}/preview-fix")
async def preview_auto_fix(
    file_id: int,
    issue_id: int,
    db: Session = Depends(get_db)
):
    """Preview what changes will be made by auto-fix."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_upload_id == file_id
        ).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        if not issue.auto_fixable:
            raise HTTPException(status_code=400, detail="Issue is not auto-fixable")
        
        # Initialize fix engine
        fix_engine = IssueFixEngine(db, file_upload)
        
        # Get preview
        preview = await fix_engine.preview_fix(issue)
        
        return {
            "issue_id": issue_id,
            "preview": preview
        }
        
    except Exception as e:
        logger.error(f"Error previewing fix: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Validate manual fix data
@router.post("/api/files/{file_id}/issues/{issue_id}/validate-fix")
async def validate_manual_fix(
    file_id: int,
    issue_id: int,
    validation_request: FixValidationRequest,
    db: Session = Depends(get_db)
):
    """Validate manual fix data before applying."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_upload_id == file_id
        ).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Initialize fix engine
        fix_engine = IssueFixEngine(db, file_upload)
        
        # Validate fix data
        validation_result = await fix_engine.validate_fix_data(issue, validation_request.fix_data)
        
        return {
            "issue_id": issue_id,
            "validation": validation_result
        }
        
    except Exception as e:
        logger.error(f"Error validating fix data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Save fix progress
@router.post("/api/files/{file_id}/fix-progress")
async def save_fix_progress(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Save current fix progress for a file."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get unresolved issues count
        unresolved_count = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_id,
            ValidationResult.is_resolved == False
        ).count()
        
        # Get resolved issues count
        resolved_count = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_id,
            ValidationResult.is_resolved == True
        ).count()
        
        return {
            "file_id": file_id,
            "unresolved_issues": unresolved_count,
            "resolved_issues": resolved_count,
            "progress_percentage": (resolved_count / (resolved_count + unresolved_count)) * 100 if (resolved_count + unresolved_count) > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error saving fix progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get current fix progress
@router.get("/api/files/{file_id}/fix-progress")
async def get_fix_progress(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Get current fix progress for a file."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get unresolved issues count
        unresolved_count = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_id,
            ValidationResult.is_resolved == False
        ).count()
        
        # Get resolved issues count
        resolved_count = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_id,
            ValidationResult.is_resolved == True
        ).count()
        
        # Get critical issues count
        critical_count = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_id,
            ValidationResult.is_resolved == False,
            ValidationResult.issue_type == 'critical'
        ).count()
        
        return {
            "file_id": file_id,
            "unresolved_issues": unresolved_count,
            "resolved_issues": resolved_count,
            "critical_issues": critical_count,
            "progress_percentage": (resolved_count / (resolved_count + unresolved_count)) * 100 if (resolved_count + unresolved_count) > 0 else 0,
            "can_proceed_to_compliance": critical_count == 0
        }
        
    except Exception as e:
        logger.error(f"Error getting fix progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Check compliance readiness
@router.get("/api/files/{file_id}/compliance-readiness")
async def check_compliance_readiness(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Check if file is ready for compliance testing after fixes."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check for unresolved critical issues
        critical_issues = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_id,
            ValidationResult.is_resolved == False,
            ValidationResult.issue_type == 'critical'
        ).all()
        
        # Check for unresolved warning issues
        warning_issues = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_id,
            ValidationResult.is_resolved == False,
            ValidationResult.issue_type == 'warning'
        ).all()
        
        return {
            "file_id": file_id,
            "ready_for_compliance": len(critical_issues) == 0,
            "critical_issues_remaining": len(critical_issues),
            "warning_issues_remaining": len(warning_issues),
            "recommendations": [
                "Resolve all critical issues before running compliance tests",
                "Review warning issues for potential compliance impact"
            ] if len(critical_issues) > 0 else [
                "File is ready for compliance testing",
                "Consider reviewing remaining warning issues"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error checking compliance readiness: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export fixed file
@router.get("/api/files/{file_id}/export")
async def export_fixed_file(
    file_id: int,
    format: str = "xlsx",
    db: Session = Depends(get_db)
):
    """Export the file with all fixes applied."""
    try:
        # Get the file upload
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Initialize fix engine
        fix_engine = IssueFixEngine(db, file_upload)
        
        # Export the fixed file
        file_content = await fix_engine.export_fixed_file(format)
        
        # Generate filename
        original_name = file_upload.original_filename
        name_without_ext = original_name.rsplit('.', 1)[0]
        export_filename = f"{name_without_ext}_fixed.{format}"
        
        return {
            "file_content": file_content,
            "filename": export_filename,
            "format": format
        }
        
    except Exception as e:
        logger.error(f"Error exporting fixed file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task to recalculate quality score
async def recalculate_quality_score(file_id: int, db: Session):
    """Recalculate data quality score after fixes."""
    try:
        # Get all issues for the file
        issues = db.query(ValidationResult).filter(
            ValidationResult.file_upload_id == file_id
        ).all()
        
        # Calculate new scores
        total_issues = len(issues)
        resolved_issues = len([i for i in issues if i.is_resolved])
        critical_issues = len([i for i in issues if i.issue_type == 'critical'])
        warning_issues = len([i for i in issues if i.issue_type == 'warning'])
        auto_fixable = len([i for i in issues if i.auto_fixable])
        
        # Calculate overall score (simplified)
        overall_score = max(0, 100 - (total_issues * 10) + (resolved_issues * 5))
        
        # Update or create quality score record
        quality_score = db.query(DataQualityScore).filter(
            DataQualityScore.file_upload_id == file_id
        ).first()
        
        if not quality_score:
            quality_score = DataQualityScore(file_upload_id=file_id)
            db.add(quality_score)
        
        quality_score.overall_score = overall_score
        quality_score.critical_issues = critical_issues
        quality_score.warning_issues = warning_issues
        quality_score.total_issues = total_issues
        quality_score.auto_fixable_issues = auto_fixable
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error recalculating quality score: {str(e)}")
        db.rollback()