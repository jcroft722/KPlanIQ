import React, { useState, useEffect } from 'react';
import './ValidationResults.css';
import { getValidationResults, autoFixIssues } from '../services/api';
import { runDataValidation, getDataQualityScore } from '../api/files';

// Types that match the backend ValidationEngine
export interface ValidationIssue {
  id: number;
  issue_type: 'critical' | 'warning' | 'info';
  severity: string;
  category: string;
  title: string;
  description: string;
  affected_rows?: number[];
  affected_employees?: string[];
  suggested_action?: string;
  auto_fixable: boolean;
  is_resolved: boolean;
  confidence_score: number;
  details?: any;
  created_at: string;
}

interface DataQualityScore {
  file_id: number;
  overall: number;
  completeness: number;
  consistency: number;
  accuracy: number;
  anomaly_count: number;
  critical_issues: number;
  warning_issues: number;
  total_issues: number;
  auto_fixable: number;
  last_updated: string | null;
}

interface ValidationResultsProps {
  fileId: number;
  onProceedToCompliance: () => void;
  onNavigateToFixIssues: () => void;
}

export const ValidationResults: React.FC<ValidationResultsProps> = ({ fileId, onProceedToCompliance, onNavigateToFixIssues }) => {
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [qualityScore, setQualityScore] = useState<DataQualityScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIssues, setSelectedIssues] = useState<number[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'critical' | 'warning' | 'anomaly'>('all');

  useEffect(() => {
    loadValidationResults();
  }, [fileId]);

  const loadValidationResults = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // First, run validation
      console.log(`Running validation for file ${fileId}...`);
      setIsValidating(true);
      try {
        await runDataValidation(fileId);
        console.log('Validation complete, fetching results...');
      } catch (err) {
        console.error('Error running validation:', err);
        throw new Error('Failed to run validation');
      } finally {
        setIsValidating(false);
      }
      
      // Then fetch the results
      const [validationData, qualityData] = await Promise.all([
        getValidationResults(fileId),
        getDataQualityScore(fileId).catch(err => {
          console.warn('Could not fetch quality score:', err);
          return null;
        })
      ]);
      
      console.log('Validation results:', validationData);
      
      if (validationData && validationData.issues) {
        setIssues(validationData.issues);
      } else {
        setIssues([]);
        console.warn('No issues found in validation data:', validationData);
      }
      
      setQualityScore(qualityData);
    } catch (err) {
      console.error('Validation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to load validation results');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoFix = async () => {
    try {
      setLoading(true);
      const result = await autoFixIssues(fileId, selectedIssues);
      await loadValidationResults();
      setSelectedIssues([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to auto-fix issues');
    } finally {
      setLoading(false);
    }
  };

  const canProceedToCompliance = !issues.some(issue => issue.issue_type === 'critical' && !issue.is_resolved);

  const filterIssues = (type: 'all' | 'critical' | 'warning' | 'anomaly') => {
    setActiveTab(type);
  };

  const filteredIssues = issues.filter(issue => {
    if (activeTab === 'all') return true;
    if (activeTab === 'critical') return issue.issue_type === 'critical';
    if (activeTab === 'warning') return issue.issue_type === 'warning';
    if (activeTab === 'anomaly') return issue.issue_type === 'info';
    return true;
  });

  const criticalCount = issues.filter(issue => issue.issue_type === 'critical').length;
  const warningCount = issues.filter(issue => issue.issue_type === 'warning').length;
  const anomalyCount = issues.filter(issue => issue.issue_type === 'info').length;
  
  if (loading) {
    return (
      <div className="loading">
        {isValidating ? 'Running validation...' : 'Loading validation results...'}
      </div>
    );
  }

  return (
    <div className="container">
      {/* Header Section */}
      <div className="header">
        <div className="header-top">
          <h1>Data Validation Results</h1>
        </div>
        
        <div className="file-info">
          <span className="file-badge">📄 {qualityScore?.file_id ? `File ID: ${qualityScore.file_id}` : 'File Data'}</span>
          <span className="file-badge">📅 Validated: {qualityScore?.last_updated || 'Just now'}</span>
          <span className="file-badge">👥 {issues.length} issues detected</span>
        </div>
        
        <div className={`status-banner ${canProceedToCompliance ? 'status-success' : 'status-warning'}`}>
          <strong>{canProceedToCompliance ? '✅ Ready for Compliance Testing:' : '⚠️ Action Required:'}</strong> 
          {canProceedToCompliance 
            ? ' All critical issues have been resolved. You can proceed to compliance testing.'
            : ' Some critical issues need attention before running compliance tests. Most can be resolved automatically or with simple corrections.'}
        </div>
        
        <div className="stats-grid">
          <div className="stat-card stat-success">
            <div className="stat-number">{qualityScore?.overall.toFixed(0) || 0}</div>
            <div className="stat-label">Quality Score</div>
          </div>
          <div className="stat-card stat-error">
            <div className="stat-number">{criticalCount}</div>
            <div className="stat-label">Critical Issues</div>
          </div>
          <div className="stat-card stat-warning">
            <div className="stat-number">{warningCount}</div>
            <div className="stat-label">Warnings</div>
          </div>
          <div className="stat-card stat-warning">
            <div className="stat-number">{anomalyCount}</div>
            <div className="stat-label">Anomalies Detected</div>
          </div>
        </div>
      </div>

      <div className="main-content">
        {/* Issues List */}
        <div className="issues-section">
          <div className="section-header">
            <h2 className="section-title">
              🔍 Data Issues
            </h2>
            <div className="filter-tabs">
              <button 
                className={`tab ${activeTab === 'all' ? 'active' : ''}`} 
                onClick={() => filterIssues('all')}
              >
                All ({issues.length})
              </button>
              <button 
                className={`tab ${activeTab === 'critical' ? 'active' : ''}`} 
                onClick={() => filterIssues('critical')}
              >
                Critical ({criticalCount})
              </button>
              <button 
                className={`tab ${activeTab === 'warning' ? 'active' : ''}`} 
                onClick={() => filterIssues('warning')}
              >
                Warnings ({warningCount})
              </button>
              <button 
                className={`tab ${activeTab === 'anomaly' ? 'active' : ''}`} 
                onClick={() => filterIssues('anomaly')}
              >
                Anomalies ({anomalyCount})
              </button>
            </div>
          </div>
          
          <div className="issues-list">
            {filteredIssues.map(issue => (
              <div key={issue.id} className="issue-item" data-type={issue.issue_type}>
                <div className="issue-header">
                  <span className={`severity-badge severity-${issue.severity.toLowerCase()}`}>
                    {issue.issue_type.charAt(0).toUpperCase() + issue.issue_type.slice(1)}
                  </span>
                  <div className="issue-title">{issue.title}</div>
                  {issue.auto_fixable && !issue.is_resolved && (
                    <button 
                      className="action-button"
                      onClick={() => setSelectedIssues([...selectedIssues, issue.id])}
                      disabled={selectedIssues.includes(issue.id)}
                    >
                      Fix Now
                    </button>
                  )}
                </div>
                <div className="issue-description">
                  {issue.description}
                </div>
                <div className="issue-details">
                  {issue.affected_employees && (
                    <span className="detail-item">👥 Affects: {issue.affected_employees} employees</span>
                  )}
                  {issue.affected_rows && issue.affected_rows.length > 0 && (
                    <span className="detail-item">📍 Rows: {issue.affected_rows.slice(0, 5).join(', ')}{issue.affected_rows.length > 5 ? '...' : ''}</span>
                  )}
                  {issue.severity === 'high' && (
                    <span className="detail-item">⚖️ Compliance Impact: High</span>
                  )}
                  {issue.auto_fixable && (
                    <span className="detail-item">🔧 Auto-fix Available</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar */}
        <div className="sidebar">
          {/* Validation Progress */}
          <div className="sidebar-card">
            <h3>Validation Progress</h3>
            <div style={{ margin: '12px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span>Data Quality</span>
                <span>{qualityScore?.overall.toFixed(0) || 0}%</span>
              </div>
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${qualityScore?.overall || 0}%` }}></div>
              </div>
            </div>
            
            <div style={{ fontSize: '14px', color: '#64748b' }}>
              <div style={{ marginBottom: '8px' }}>✅ Format validation complete</div>
              <div style={{ marginBottom: '8px' }}>✅ Field mapping verified</div>
              <div style={{ marginBottom: '8px' }}>
                {issues.length > 0 
                  ? `⚠️ ${issues.length} issues need attention` 
                  : '✅ No issues detected'}
              </div>
              <div>
                {canProceedToCompliance 
                  ? '✅ Ready for compliance testing' 
                  : '⏳ Ready for compliance testing after fixes'}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="sidebar-card">
            <h3>Quick Actions</h3>
            <div className="action-buttons">
              {selectedIssues.length > 0 ? (
                <button className="btn btn-primary" onClick={handleAutoFix}>
                  🔧 Auto-Fix Selected Issues ({selectedIssues.length})
                </button>
              ) : (
                <button className="btn btn-primary" onClick={() => {
                  const autoFixableIssues = issues
                    .filter(issue => issue.auto_fixable && !issue.is_resolved)
                    .map(issue => issue.id);
                  setSelectedIssues(autoFixableIssues);
                  if (autoFixableIssues.length > 0) {
                    handleAutoFix();
                  }
                }}>
                  🔧 Auto-Fix Simple Issues
                </button>
              )}
              <button className="btn btn-secondary">📥 Download Error Report</button>
              <button className="btn btn-secondary">💾 Save Progress</button>
              <button className={`btn ${canProceedToCompliance ? 'btn-primary' : 'btn-disabled'}`}
                  onClick={canProceedToCompliance ? onProceedToCompliance : onNavigateToFixIssues}
                  disabled={false} // Always allow navigation to fix issues
                >
                  {canProceedToCompliance ? 'Proceed to Compliance Testing →' : 'Fix Critical Issues →'}

              </button>
            </div>
          </div>

          {/* Next Steps */}
          <div className="sidebar-card">
            <div className="next-steps">
              <h4>Next Steps</h4>
              <ul>
                {criticalCount > 0 && <li>Fix {criticalCount} critical issues to proceed</li>}
                {warningCount > 0 && <li>Review flagged warnings</li>}
                <li>Then run compliance tests</li>
              </ul>
            </div>
            
            <div className="compliance-impact">
              <h4 style={{ color: '#92400e', marginBottom: '8px' }}>⚖️ Compliance Impact</h4>
              <div style={{ fontSize: '14px', color: '#92400e' }}>
                Current issues may affect:
                <br/>• HCE determination
                <br/>• 410(b) coverage testing
                <br/>• ADP/ACP calculations
              </div>
            </div>
          </div>

          {/* Help */}
          <div className="sidebar-card">
            <h3>Need Help?</h3>
            <div style={{ fontSize: '14px', color: '#64748b', marginBottom: '12px' }}>
              Our validation system checks for common data issues that could affect your plan's compliance testing.
            </div>
            <button className="btn btn-secondary">📚 View Data Guidelines</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ValidationResults;