# fix_engine.py - Issue Fix Engine for KPlanIQ

import pandas as pd
import numpy as np
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
import io

from ..models.models import FileUpload, ValidationResult
from .validation_engine import DataValidationEngine

logger = logging.getLogger(__name__)

class IssueFixEngine:
    """Engine for applying fixes to validation issues."""
    
    def __init__(self, db: Session, file_upload: FileUpload):
        self.db = db
        self.file_upload = file_upload
        self.df = self._load_dataframe()
        
    def _load_dataframe(self) -> pd.DataFrame:
        """Load the file data into a pandas DataFrame."""
        try:
            if self.file_upload.file_path.endswith('.xlsx'):
                return pd.read_excel(self.file_upload.file_path)
            elif self.file_upload.file_path.endswith('.csv'):
                return pd.read_csv(self.file_upload.file_path)
            else:
                raise ValueError(f"Unsupported file format: {self.file_upload.file_path}")
        except Exception as e:
            logger.error(f"Error loading dataframe: {str(e)}")
            raise
    
    async def apply_fix(self, issue: ValidationResult, action_type: str, fix_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply a fix to a validation issue."""
        try:
            if action_type == 'auto_fix':
                return await self._apply_auto_fix(issue)
            elif action_type == 'manual_entry':
                return await self._apply_manual_fix(issue, fix_data)
            elif action_type == 'exclude':
                return await self._apply_exclusion(issue)
            elif action_type == 'accept':
                return await self._apply_acceptance(issue)
            elif action_type == 'generate_test':
                return await self._generate_test_data(issue)
            else:
                raise ValueError(f"Unknown action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Error applying fix: {str(e)}")
            raise
    
    async def _apply_auto_fix(self, issue: ValidationResult) -> Dict[str, Any]:
        """Apply automatic fix based on issue type."""
        if not issue.auto_fixable:
            raise ValueError("Issue is not auto-fixable")
        
        issue_details = json.loads(issue.details) if issue.details else {}
        affected_rows = issue.affected_rows or []
        
        results = []
        
        if issue.category == 'Format Error':
            if 'date' in issue.title.lower():
                results = self._fix_date_formats(affected_rows)
            elif 'ssn' in issue.title.lower():
                results = self._fix_ssn_formats(affected_rows)
            elif 'numeric' in issue.title.lower():
                results = self._fix_numeric_formats(affected_rows, issue_details)
                
        elif issue.category == 'Missing Data':
            if issue.title == 'Missing Required Fields':
                results = self._fix_missing_required_fields(affected_rows, issue_details)
        
        # Save changes to file
        await self._save_dataframe()
        
        return {
            "action": "auto_fix",
            "affected_rows": len(affected_rows),
            "changes_applied": len(results),
            "details": results
        }
    
    def _fix_date_formats(self, affected_rows: List[int]) -> List[Dict[str, Any]]:
        """Fix date format issues."""
        results = []
        date_columns = ['DOB', 'DOH', 'DOT', 'HireDate', 'TermDate', 'DateOfBirth']
        
        for row_idx in affected_rows:
            if row_idx >= len(self.df):
                continue
                
            for col in date_columns:
                if col in self.df.columns:
                    original_value = self.df.at[row_idx, col]
                    if pd.isna(original_value):
                        continue
                        
                    # Try to parse and standardize date
                    fixed_value = self._standardize_date(str(original_value))
                    if fixed_value and fixed_value != original_value:
                        self.df.at[row_idx, col] = fixed_value
                        results.append({
                            "row": row_idx,
                            "column": col,
                            "original": str(original_value),
                            "fixed": fixed_value
                        })
        
        return results
    
    def _standardize_date(self, date_str: str) -> Optional[str]:
        """Standardize date string to MM/DD/YYYY format."""
        # Common date patterns
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or MM-DD-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2})',  # MM/DD/YY
            r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})',  # Month DD, YYYY
            r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})',  # DD Month YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        # Try to parse with pandas
                        parsed_date = pd.to_datetime(date_str, errors='coerce')
                        if not pd.isna(parsed_date):
                            return parsed_date.strftime('%m/%d/%Y')
                except:
                    continue
        
        return None
    
    def _fix_ssn_formats(self, affected_rows: List[int]) -> List[Dict[str, Any]]:
        """Fix SSN format issues."""
        results = []
        ssn_columns = ['SSN', 'SocialSecurityNumber', 'EmpSSN']
        
        for row_idx in affected_rows:
            if row_idx >= len(self.df):
                continue
                
            for col in ssn_columns:
                if col in self.df.columns:
                    original_value = self.df.at[row_idx, col]
                    if pd.isna(original_value):
                        continue
                        
                    # Standardize SSN format
                    fixed_value = self._standardize_ssn(str(original_value))
                    if fixed_value and fixed_value != original_value:
                        self.df.at[row_idx, col] = fixed_value
                        results.append({
                            "row": row_idx,
                            "column": col,
                            "original": str(original_value),
                            "fixed": fixed_value
                        })
        
        return results
    
    def _standardize_ssn(self, ssn_str: str) -> Optional[str]:
        """Standardize SSN to XXX-XX-XXXX format."""
        # Remove all non-digits
        digits = re.sub(r'\D', '', ssn_str)
        
        if len(digits) == 9:
            return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
        
        return None
    
    def _fix_numeric_formats(self, affected_rows: List[int], issue_details: Dict) -> List[Dict[str, Any]]:
        """Fix numeric format issues."""
        results = []
        numeric_columns = ['PriorYearComp', 'Compensation', 'Salary', 'EmployeeDeferrals', 'EmployerMatch']
        
        for row_idx in affected_rows:
            if row_idx >= len(self.df):
                continue
                
            for col in numeric_columns:
                if col in self.df.columns:
                    original_value = self.df.at[row_idx, col]
                    if pd.isna(original_value):
                        continue
                        
                    # Clean numeric value
                    fixed_value = self._clean_numeric(str(original_value))
                    if fixed_value is not None and fixed_value != original_value:
                        self.df.at[row_idx, col] = fixed_value
                        results.append({
                            "row": row_idx,
                            "column": col,
                            "original": str(original_value),
                            "fixed": str(fixed_value)
                        })
        
        return results
    
    def _clean_numeric(self, value_str: str) -> Optional[float]:
        """Clean and convert string to numeric value."""
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[$,\s%]', '', value_str)
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    async def _apply_manual_fix(self, issue: ValidationResult, fix_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply manual fixes based on provided data."""
        results = []
        
        if 'ssn_fixes' in fix_data:
            # Apply SSN fixes
            for row_idx, ssn_value in fix_data['ssn_fixes'].items():
                row_idx = int(row_idx)
                if row_idx < len(self.df):
                    # Find SSN column
                    ssn_col = None
                    for col in ['SSN', 'SocialSecurityNumber', 'EmpSSN']:
                        if col in self.df.columns:
                            ssn_col = col
                            break
                    
                    if ssn_col:
                        original_value = self.df.at[row_idx, ssn_col]
                        self.df.at[row_idx, ssn_col] = ssn_value
                        results.append({
                            "row": row_idx,
                            "column": ssn_col,
                            "original": str(original_value) if not pd.isna(original_value) else "MISSING",
                            "fixed": ssn_value
                        })
        
        if 'compensation' in fix_data:
            # Apply compensation fixes
            comp_columns = ['PriorYearComp', 'Compensation', 'Salary']
            affected_rows = issue.affected_rows or []
            
            for row_idx in affected_rows:
                if row_idx < len(self.df):
                    for col in comp_columns:
                        if col in self.df.columns:
                            original_value = self.df.at[row_idx, col]
                            numeric_value = float(fix_data['compensation'].replace('$', '').replace(',', ''))
                            self.df.at[row_idx, col] = numeric_value
                            results.append({
                                "row": row_idx,
                                "column": col,
                                "original": str(original_value),
                                "fixed": str(numeric_value)
                            })
                            break
        
        # Save changes
        await self._save_dataframe()
        
        return {
            "action": "manual_fix",
            "changes_applied": len(results),
            "details": results
        }
    
    async def _apply_exclusion(self, issue: ValidationResult) -> Dict[str, Any]:
        """Mark affected rows for exclusion from testing."""
        affected_rows = issue.affected_rows or []
        
        # Add exclusion flag column if it doesn't exist
        if 'exclude_from_testing' not in self.df.columns:
            self.df['exclude_from_testing'] = False
        
        # Mark rows for exclusion
        for row_idx in affected_rows:
            if row_idx < len(self.df):
                self.df.at[row_idx, 'exclude_from_testing'] = True
        
        await self._save_dataframe()
        
        return {
            "action": "exclude",
            "excluded_rows": len(affected_rows),
            "details": f"Excluded {len(affected_rows)} rows from compliance testing"
        }
    
    async def _apply_acceptance(self, issue: ValidationResult) -> Dict[str, Any]:
        """Accept the issue as valid - no data changes needed."""
        return {
            "action": "accept",
            "message": "Issue accepted as valid - no changes made",
            "details": f"Accepted: {issue.title}"
        }
    
    async def _generate_test_data(self, issue: ValidationResult) -> Dict[str, Any]:
        """Generate test data for missing fields."""
        if 'ssn' in issue.title.lower():
            return await self._generate_test_ssns(issue)
        elif 'compensation' in issue.title.lower():
            return await self._generate_test_compensation(issue)
        else:
            raise ValueError(f"Cannot generate test data for issue type: {issue.title}")
    
    async def _generate_test_ssns(self, issue: ValidationResult) -> Dict[str, Any]:
        """Generate test SSNs for missing values."""
        affected_rows = issue.affected_rows or []
        results = []
        
        # Generate unique test SSNs
        base_ssn = 123456789
        ssn_col = None
        
        # Find SSN column
        for col in ['SSN', 'SocialSecurityNumber', 'EmpSSN']:
            if col in self.df.columns:
                ssn_col = col
                break
        
        if not ssn_col:
            raise ValueError("No SSN column found")
        
        for i, row_idx in enumerate(affected_rows):
            if row_idx < len(self.df):
                test_ssn_num = base_ssn + i
                test_ssn = f"{str(test_ssn_num)[:3]}-{str(test_ssn_num)[3:5]}-{str(test_ssn_num)[5:]}"
                
                original_value = self.df.at[row_idx, ssn_col]
                self.df.at[row_idx, ssn_col] = test_ssn
                
                results.append({
                    "row": row_idx,
                    "column": ssn_col,
                    "original": str(original_value) if not pd.isna(original_value) else "MISSING",
                    "generated": test_ssn
                })
        
        await self._save_dataframe()
        
        return {
            "action": "generate_test_ssns",
            "generated_count": len(results),
            "details": results
        }
    
    async def _save_dataframe(self):
        """Save the modified dataframe back to file."""
        try:
            if self.file_upload.file_path.endswith('.xlsx'):
                self.df.to_excel(self.file_upload.file_path, index=False)
            elif self.file_upload.file_path.endswith('.csv'):
                self.df.to_csv(self.file_upload.file_path, index=False)
                
            # Update file modification time
            self.file_upload.updated_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error saving dataframe: {str(e)}")
            raise
    
    async def get_fix_suggestions(self, issue: ValidationResult) -> List[Dict[str, Any]]:
        """Get suggested fixes for an issue."""
        suggestions = []
        
        if issue.auto_fixable:
            suggestions.append({
                "type": "auto_fix",
                "title": "Auto-Fix",
                "description": "Automatically fix this issue using built-in rules",
                "confidence": issue.confidence_score
            })
        
        if issue.category == 'Missing Data':
            suggestions.extend([
                {
                    "type": "manual_entry",
                    "title": "Manual Entry",
                    "description": "Manually enter the missing data",
                    "confidence": 1.0
                },
                {
                    "type": "exclude",
                    "title": "Exclude from Testing",
                    "description": "Exclude affected records from compliance tests",
                    "confidence": 0.8
                },
                {
                    "type": "generate_test",
                    "title": "Generate Test Data",
                    "description": "Generate test data for development/testing purposes",
                    "confidence": 0.6
                }
            ])
        
        elif issue.category == 'Anomaly':
            suggestions.extend([
                {
                    "type": "accept",
                    "title": "Accept as Valid",
                    "description": "Mark this anomaly as acceptable for your organization",
                    "confidence": 0.7
                },
                {
                    "type": "manual_entry",
                    "title": "Correct Value",
                    "description": "Manually correct the anomalous value",
                    "confidence": 0.9
                }
            ])
        
        return suggestions
    
    async def preview_fix(self, issue: ValidationResult) -> Dict[str, Any]:
        """Preview what changes will be made by auto-fix."""
        if not issue.auto_fixable:
            raise ValueError("Issue is not auto-fixable")
        
        # Create a copy of the dataframe for preview
        preview_df = self.df.copy()
        original_df = self.df
        
        try:
            # Temporarily use preview dataframe
            self.df = preview_df
            
            # Apply fix to preview
            fix_result = await self._apply_auto_fix(issue)
            
            # Generate preview comparison
            preview = {
                "changes": fix_result["details"],
                "summary": {
                    "affected_rows": fix_result["affected_rows"],
                    "changes_count": fix_result["changes_applied"]
                }
            }
            
            return preview
            
        finally:
            # Restore original dataframe
            self.df = original_df
    
    async def validate_fix_data(self, issue: ValidationResult, fix_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate manual fix data before applying."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        if 'ssn_fixes' in fix_data:
            for row_idx, ssn_value in fix_data['ssn_fixes'].items():
                if not self._is_valid_ssn(ssn_value):
                    validation_results["valid"] = False
        
        if 'compensation' in fix_data:
            try:
                comp_value = float(str(fix_data['compensation']).replace(', ', '').replace(',', ''))
                if comp_value < 0:
                    validation_results["valid"] = False
                    validation_results["errors"].append("Compensation cannot be negative")
                elif comp_value > 10000000:  # $10M limit
                    validation_results["warnings"].append("Compensation value is unusually high")
            except ValueError:
                validation_results["valid"] = False
                validation_results["errors"].append("Invalid compensation format")
        
        return validation_results
    
    def _is_valid_ssn(self, ssn: str) -> bool:
        """Validate SSN format."""
        # Check for XXX-XX-XXXX format
        pattern = r'^\d{3}-\d{2}-\d{4}$'
        if not re.match(pattern, ssn):
            return False
        
        # Check for invalid SSNs (all zeros, etc.)
        digits = ssn.replace('-', '')
        if digits == '000000000' or digits == '999999999':
            return False
        
        return True
    
    async def export_fixed_file(self, format: str = 'xlsx') -> bytes:
        """Export the file with all fixes applied."""
        try:
            output = io.BytesIO()
            
            if format.lower() == 'xlsx':
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    self.df.to_excel(writer, index=False, sheet_name='Fixed_Data')
            elif format.lower() == 'csv':
                self.df.to_csv(output, index=False)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error exporting fixed file: {str(e)}")
            raise
    
    async def get_issue_fix_history(self, issue: ValidationResult) -> List[Dict[str, Any]]:
        """Get the fix history for an issue."""
        # This would typically come from a separate audit table
        # For now, return basic info from the ValidationResult
        history = []
        
        if issue.is_resolved:
            history.append({
                "timestamp": issue.updated_at or issue.created_at,
                "action": issue.resolution_method or "resolved",
                "user": "current_user",  # Would come from actual user context
                "details": json.loads(issue.resolution_data) if issue.resolution_data else None
            })
        
        return history
    
    async def undo_issue_fix(self, issue: ValidationResult) -> Dict[str, Any]:
        """Undo a previously applied fix."""
        if not issue.is_resolved:
            raise ValueError("Issue is not resolved, cannot undo")
        
        # This would require storing original values before fixes
        # For now, just mark as unresolved
        issue.is_resolved = False
        issue.resolution_method = None
        issue.resolution_data = None
        
        self.db.commit()
        
        return {
            "success": True,
            "message": "Fix undone - issue marked as unresolved",
            "note": "Original data restoration requires backup implementation"
        }


class FixPreviewEngine:
    """Engine for previewing fixes without applying them."""
    
    def __init__(self, original_df: pd.DataFrame):
        self.original_df = original_df.copy()
        self.preview_df = original_df.copy()
    
    def preview_date_fix(self, row_indices: List[int], column: str) -> Dict[str, Any]:
        """Preview date format fixes."""
        changes = []
        
        for row_idx in row_indices:
            if row_idx < len(self.preview_df) and column in self.preview_df.columns:
                original = self.preview_df.at[row_idx, column]
                if not pd.isna(original):
                    fixed = self._standardize_date(str(original))
                    if fixed and fixed != str(original):
                        changes.append({
                            "row": row_idx,
                            "original": str(original),
                            "preview": fixed
                        })
        
        return {
            "type": "date_format",
            "column": column,
            "changes": changes
        }
    
    def preview_ssn_fix(self, row_indices: List[int], column: str) -> Dict[str, Any]:
        """Preview SSN format fixes."""
        changes = []
        
        for row_idx in row_indices:
            if row_idx < len(self.preview_df) and column in self.preview_df.columns:
                original = self.preview_df.at[row_idx, column]
                if not pd.isna(original):
                    fixed = self._standardize_ssn(str(original))
                    if fixed and fixed != str(original):
                        changes.append({
                            "row": row_idx,
                            "original": str(original),
                            "preview": fixed
                        })
        
        return {
            "type": "ssn_format",
            "column": column,
            "changes": changes
        }
    
    def _standardize_date(self, date_str: str) -> Optional[str]:
        """Standardize date string - same logic as main engine."""
        try:
            parsed_date = pd.to_datetime(date_str, errors='coerce')
            if not pd.isna(parsed_date):
                return parsed_date.strftime('%m/%d/%Y')
        except:
            pass
        return None
    
    def _standardize_ssn(self, ssn_str: str) -> Optional[str]:
        """Standardize SSN format - same logic as main engine."""
        digits = re.sub(r'\D', '', ssn_str)
        if len(digits) == 9:
            return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
        return None


class BulkFixEngine:
    """Engine for applying bulk fixes efficiently."""
    
    def __init__(self, fix_engine: IssueFixEngine):
        self.fix_engine = fix_engine
        
    async def apply_all_auto_fixes(self, issues: List[ValidationResult]) -> Dict[str, Any]:
        """Apply all auto-fixable issues in bulk."""
        auto_fixable_issues = [issue for issue in issues if issue.auto_fixable and not issue.is_resolved]
        
        if not auto_fixable_issues:
            return {
                "success": True,
                "message": "No auto-fixable issues found",
                "applied_fixes": 0
            }
        
        results = []
        successful_fixes = 0
        
        for issue in auto_fixable_issues:
            try:
                fix_result = await self.fix_engine.apply_fix(issue, 'auto_fix')
                issue.is_resolved = True
                issue.resolution_method = 'auto_fix'
                results.append({
                    "issue_id": issue.id,
                    "success": True,
                    "result": fix_result
                })
                successful_fixes += 1
                
            except Exception as e:
                logger.error(f"Error in bulk fix for issue {issue.id}: {str(e)}")
                results.append({
                    "issue_id": issue.id,
                    "success": False,
                    "error": str(e)
                })
        
        # Single save operation for efficiency
        await self.fix_engine._save_dataframe()
        self.fix_engine.db.commit()
        
        return {
            "success": True,
            "message": f"Applied {successful_fixes} of {len(auto_fixable_issues)} auto-fixes",
            "applied_fixes": successful_fixes,
            "total_attempted": len(auto_fixable_issues),
            "results": results
        }
    
    async def apply_category_fixes(self, issues: List[ValidationResult], category: str) -> Dict[str, Any]:
        """Apply fixes for all issues in a specific category."""
        category_issues = [
            issue for issue in issues 
            if issue.category == category and not issue.is_resolved
        ]
        
        if not category_issues:
            return {
                "success": True,
                "message": f"No unresolved issues found in category: {category}",
                "applied_fixes": 0
            }
        
        results = []
        successful_fixes = 0
        
        for issue in category_issues:
            try:
                if issue.auto_fixable:
                    fix_result = await self.fix_engine.apply_fix(issue, 'auto_fix')
                    issue.is_resolved = True
                    issue.resolution_method = 'auto_fix'
                    successful_fixes += 1
                    
                    results.append({
                        "issue_id": issue.id,
                        "success": True,
                        "result": fix_result
                    })
                else:
                    results.append({
                        "issue_id": issue.id,
                        "success": False,
                        "error": "Issue requires manual fix"
                    })
                    
            except Exception as e:
                logger.error(f"Error in category fix for issue {issue.id}: {str(e)}")
                results.append({
                    "issue_id": issue.id,
                    "success": False,
                    "error": str(e)
                })
        
        if successful_fixes > 0:
            await self.fix_engine._save_dataframe()
            self.fix_engine.db.commit()
        
        return {
            "success": True,
            "message": f"Applied {successful_fixes} fixes in category: {category}",
            "applied_fixes": successful_fixes,
            "total_attempted": len(category_issues),
            "results": results
        }