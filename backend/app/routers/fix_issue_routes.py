# fix_issues_routes.py - FastAPI routes for Fix Issues functionality

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import logging

from ..database import get_db
from ..models import FileUpload, ValidationResult, DataQualityScore, User
from ..auth import get_current_user
from ..validation_engine import DataValidationEngine
from ..fix_engine import IssueFixEngine

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply a fix to a specific validation issue."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_id == file_id
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Apply auto-fixes to multiple issues at once."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issues
        issues = db.query(ValidationResult).filter(
            ValidationResult.id.in_(bulk_request.issue_ids),
            ValidationResult.file_id == file_id,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the status of a validation issue."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_id == file_id
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

# Get fix suggestions
@router.get("/api/files/{file_id}/issues/{issue_id}/suggestions")
async def get_fix_suggestions(
    file_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get suggested fixes for a validation issue."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_id == file_id
        ).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Initialize fix engine
        fix_engine = IssueFixEngine(db, file_upload)
        
        # Get suggestions
        suggestions = await fix_engine.get_fix_suggestions(issue)
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error getting fix suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Preview auto-fix
@router.get("/api/files/{file_id}/issues/{issue_id}/preview-fix")
async def preview_auto_fix(
    file_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview what changes will be made by auto-fix."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_id == file_id
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
            "success": True,
            "preview": preview
        }
        
    except Exception as e:
        logger.error(f"Error previewing fix: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Validate manual fix
@router.post("/api/files/{file_id}/issues/{issue_id}/validate-fix")
async def validate_manual_fix(
    file_id: int,
    issue_id: int,
    validation_request: FixValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate manual fix data before applying."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get the issue
        issue = db.query(ValidationResult).filter(
            ValidationResult.id == issue_id,
            ValidationResult.file_id == file_id
        ).first()
        
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        # Initialize fix engine
        fix_engine = IssueFixEngine(db, file_upload)
        
        # Validate fix data
        validation_result = await fix_engine.validate_fix_data(issue, validation_request.fix_data)
        
        return {
            "success": True,
            "validation": validation_result
        }
        
    except Exception as e:
        logger.error(f"Error validating fix: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Save fix progress
@router.post("/api/files/{file_id}/fix-progress")
async def save_fix_progress(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save current fix progress."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Update last modified timestamp
        file_upload.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Progress saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error saving progress: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Get fix progress
@router.get("/api/files/{file_id}/fix-progress")
async def get_fix_progress(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current fix progress."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get issue counts
        total_issues = db.query(ValidationResult).filter(
            ValidationResult.file_id == file_id
        ).count()
        
        resolved_issues = db.query(ValidationResult).filter(
            ValidationResult.file_id == file_id,
            ValidationResult.is_resolved == True
        ).count()
        
        critical_unresolved = db.query(ValidationResult).filter(
            ValidationResult.file_id == file_id,
            ValidationResult.issue_type == 'critical',
            ValidationResult.is_resolved == False
        ).count()
        
        return {
            "success": True,
            "progress": {
                "total_issues": total_issues,
                "resolved_issues": resolved_issues,
                "remaining_issues": total_issues - resolved_issues,
                "critical_unresolved": critical_unresolved,
                "completion_percentage": (resolved_issues / total_issues * 100) if total_issues > 0 else 100,
                "can_proceed_to_compliance": critical_unresolved == 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting fix progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Check compliance readiness
@router.get("/api/files/{file_id}/compliance-readiness")
async def check_compliance_readiness(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if file is ready for compliance testing."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Check for blocking issues
        critical_issues = db.query(ValidationResult).filter(
            ValidationResult.file_id == file_id,
            ValidationResult.issue_type == 'critical',
            ValidationResult.is_resolved == False
        ).all()
        
        blocking_categories = ['Missing Data', 'Format Error', 'Logic Error']
        blocking_issues = [
            issue for issue in critical_issues 
            if issue.category in blocking_categories
        ]
        
        return {
            "success": True,
            "ready": len(blocking_issues) == 0,
            "blocking_issues": len(blocking_issues),
            "blocking_issue_details": [
                {
                    "id": issue.id,
                    "title": issue.title,
                    "category": issue.category
                }
                for issue in blocking_issues
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export file with fixes applied."""
    try:
        # Verify file ownership
        file_upload = db.query(FileUpload).filter(
            FileUpload.id == file_id,
            FileUpload.user_id == current_user.id
        ).first()
        
        if not file_upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Initialize fix engine
        fix_engine = IssueFixEngine(db, file_upload)
        
        # Export file with fixes
        file_data = await fix_engine.export_fixed_file(format)
        
        # Return file as response
        from fastapi.responses import Response
        
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
        filename = f"{file_upload.original_filename}_fixed.{format}"
        
        return Response(
            content=file_data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exporting fixed file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task to recalculate quality score
async def recalculate_quality_score(file_id: int, db: Session):
    """Recalculate data quality score after fixes are applied."""
    try:
        file_upload = db.query(FileUpload).filter(FileUpload.id == file_id).first()
        if file_upload:
            validation_engine = DataValidationEngine(db, file_upload)
            await validation_engine.calculate_quality_score()
            
    except Exception as e:
        logger.error(f"Error recalculating quality score: {str(e)}")

# Add datetime import
from datetime import datetime