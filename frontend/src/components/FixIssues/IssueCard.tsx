import React, { useState } from 'react';
import './IssueCard.css';
import { ValidationIssue } from './FixIssues';

interface IssueCardProps {
  issue: ValidationIssue;
  isExpanded: boolean;
  onToggleExpansion: () => void;
  onAutoFix: () => void;
  onManualFix: (fixData: any) => void;
  onAccept: () => void;
  manualFixData: any;
  onUpdateManualFixData: (field: string, value: any) => void;
  saving: boolean;
}

export const IssueCard: React.FC<IssueCardProps> = ({
  issue,
  isExpanded,
  onToggleExpansion,
  onAutoFix,
  onManualFix,
  onAccept,
  manualFixData,
  onUpdateManualFixData,
  saving
}) => {
  const [localFixData, setLocalFixData] = useState<any>({});

  const getSeverityBadgeClass = (type: string) => {
    switch (type) {
      case 'critical': return 'severity-critical-badge';
      case 'warning': return 'severity-warning-badge';
      case 'info': return 'severity-info-badge';
      default: return 'severity-info-badge';
    }
  };

  const getStatusIcon = () => {
    if (issue.is_resolved) {
      return <span className="status-icon status-fixed">✓</span>;
    }
    return <span className="status-icon status-pending">⚠</span>;
  };

  const handleSSNInput = (rowIndex: number, value: string) => {
    // Format SSN as user types
    let formatted = value.replace(/\D/g, '');
    if (formatted.length >= 9) {
      formatted = formatted.substring(0, 9);
      formatted = formatted.replace(/(\d{3})(\d{2})(\d{4})/, '$1-$2-$3');
    }
    
    const newData = {
      ...localFixData,
      ssn_fixes: {
        ...localFixData.ssn_fixes,
        [rowIndex]: formatted
      }
    };
    
    setLocalFixData(newData);
    onUpdateManualFixData('ssn_fixes', newData.ssn_fixes);
  };

  const handleCompensationInput = (value: string) => {
    const numericValue = value.replace(/[$,]/g, '');
    setLocalFixData({
      ...localFixData,
      compensation: numericValue
    });
    onUpdateManualFixData('compensation', numericValue);
  };

  const generateTestSSNs = () => {
    const testSSNs = ['123-45-6789', '987-65-4321', '555-12-3456'];
    const ssnFixes: any = {};
    
    if (issue.affected_rows) {
      issue.affected_rows.forEach((row, index) => {
        ssnFixes[row] = testSSNs[index] || '999-99-9999';
      });
    }
    
    setLocalFixData({
      ...localFixData,
      ssn_fixes: ssnFixes
    });
    
    setTimeout(() => {
      onManualFix({ ssn_fixes: ssnFixes });
    }, 500);
  };

  const applyManualFix = () => {
    onManualFix(localFixData);
  };

  const canApplyManualFix = () => {
    if (issue.category === 'Missing Data' && issue.title.includes('Social Security')) {
      const ssnFixes = localFixData.ssn_fixes || {};
      return issue.affected_rows?.every(row => 
        ssnFixes[row] && ssnFixes[row].length === 11
      );
    }
    
    if (issue.category === 'Anomaly' && issue.title.includes('Compensation')) {
      return localFixData.compensation && localFixData.compensation.length > 0;
    }
    
    return false;
  };

  const renderFixInterface = () => {
    if (issue.is_resolved) {
      return (
        <div className="fix-interface auto-fix">
          <div className="fix-type-header auto">
            ✅ Issue Resolved
          </div>
          <p style={{ color: '#047857', fontSize: '14px' }}>
            This issue has been successfully fixed.
          </p>
        </div>
      );
    }

    // Auto-fixable issues (format errors, etc.)
    if (issue.auto_fixable) {
      return (
        <div className="fix-interface auto-fix">
          <div className="fix-type-header auto">
            🔧 Auto-Fix Available
          </div>
          
          {issue.details?.preview && (
            <div className="auto-fix-preview">
              {Object.entries(issue.details.preview).map(([key, value]: [string, any]) => (
                <div key={key} className="preview-row">
                  <span>{key}: </span>
                  <span className="preview-before">"{value.before}"</span>
                  <span className="preview-arrow">→</span>
                  <span className="preview-after">"{value.after}"</span>
                </div>
              ))}
            </div>
          )}
          
          <div className="quick-fixes">
            <button 
              className="quick-fix-btn auto-fix-btn" 
              onClick={onAutoFix}
              disabled={saving}
            >
              {saving ? '🔄 Fixing...' : '✅ Apply Auto-Fix'}
            </button>
          </div>
        </div>
      );
    }

    // Manual fix for missing SSNs
    if (issue.category === 'Missing Data' && issue.title.includes('Social Security')) {
      return (
        <div className="fix-interface manual-fix">
          <div className="fix-type-header manual">
            📝 Manual Fix Required
          </div>
          
          <table className="data-table">
            <thead>
              <tr>
                <th>Row</th>
                <th>Employee</th>
                <th>Employee ID</th>
                <th>Social Security Number</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {issue.affected_rows?.map((row, index) => (
                <tr key={row}>
                  <td>{row}</td>
                  <td>{issue.affected_employees?.[index] || `Employee ${index + 1}`}</td>
                  <td>EMP{String(index + 1).padStart(3, '0')}</td>
                  <td className="error-cell">
                    <input
                      type="text"
                      className={localFixData.ssn_fixes?.[row] ? 'fixed-input' : 'error-input'}
                      placeholder="XXX-XX-XXXX"
                      value={localFixData.ssn_fixes?.[row] || ''}
                      onChange={(e) => handleSSNInput(row, e.target.value)}
                      maxLength={11}
                    />
                  </td>
                  <td>Active</td>
                </tr>
              ))}
            </tbody>
          </table>
          
          <div className="quick-fixes">
            <button 
              className="quick-fix-btn auto-fix-btn" 
              onClick={generateTestSSNs}
              disabled={saving}
            >
              🎯 Generate Test SSNs
            </button>
            <button 
              className="quick-fix-btn manual-fix-btn" 
              onClick={applyManualFix}
              disabled={saving || !canApplyManualFix()}
            >
              💾 Apply Manual Fix
            </button>
            <button 
              className="quick-fix-btn accept-btn" 
              onClick={() => onManualFix({ action: 'exclude' })}
              disabled={saving}
            >
              ⏭️ Exclude from Testing
            </button>
          </div>
        </div>
      );
    }

    // Manual fix for compensation issues
    if (issue.category === 'Anomaly' && issue.title.includes('Compensation')) {
      const originalValue = issue.details?.original_value || '$290,000';
      const previousValue = issue.details?.previous_value || '$65,000';
      
      return (
        <div className="fix-interface manual-fix">
          <div className="fix-type-header manual">
            📋 Review & Verify
          </div>
          
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Previous Comp</th>
                <th>Current Comp</th>
                <th>Increase</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{issue.affected_employees?.[0] || 'Employee'}</td>
                <td>{previousValue}</td>
                <td className="error-cell">
                  <input
                    type="text"
                    className="error-input"
                    value={localFixData.compensation || originalValue}
                    onChange={(e) => handleCompensationInput(e.target.value)}
                    placeholder="$0"
                  />
                </td>
                <td id="increase-calc">
                  {localFixData.compensation ? 
                    Math.round(((parseFloat(localFixData.compensation) - 65000) / 65000) * 100) + '%' :
                    '347%'
                  }
                </td>
                <td>
                  <div className="quick-fixes">
                    <button 
                      className="quick-fix-btn accept-btn" 
                      onClick={onAccept}
                      disabled={saving}
                    >
                      ✅ Correct
                    </button>
                    <button 
                      className="quick-fix-btn auto-fix-btn" 
                      onClick={() => {
                        setLocalFixData({ ...localFixData, compensation: '85000' });
                        setTimeout(() => onManualFix({ compensation: '85000' }), 500);
                      }}
                      disabled={saving}
                    >
                      🔄 Suggest Fix
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      );
    }

    // Default fix interface for other issues
    return (
      <div className="fix-interface">
        <div className="fix-type-header">
          ℹ️ Review Required
        </div>
        
        <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '12px' }}>
          {issue.description}
        </p>
        
        <div className="quick-fixes">
          <button 
            className="quick-fix-btn accept-btn" 
            onClick={onAccept}
            disabled={saving}
          >
            ✅ Accept as Valid
          </button>
          {issue.auto_fixable && (
            <button 
              className="quick-fix-btn auto-fix-btn" 
              onClick={onAutoFix}
              disabled={saving}
            >
              🔧 Auto-Fix
            </button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={`issue-card ${issue.is_resolved ? 'resolved' : ''}`}>
      <div className="issue-header">
        <div className={`issue-severity ${getSeverityBadgeClass(issue.issue_type)}`}>
          {issue.issue_type.charAt(0).toUpperCase() + issue.issue_type.slice(1)}
        </div>
        <div className="issue-title">{issue.title}</div>
        <div className="issue-meta">
          {issue.affected_rows?.length} rows • {issue.auto_fixable ? 'Auto-fixable' : 'Manual review'}
          {getStatusIcon()}
        </div>
      </div>

      {/* Always show the fix interface, no expansion needed */}
      {renderFixInterface()}
    </div>
  );
};

export default IssueCard;