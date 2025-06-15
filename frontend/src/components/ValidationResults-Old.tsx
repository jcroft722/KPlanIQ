import React, { useState, useEffect } from 'react';

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
}

export const ValidationResults: React.FC<ValidationResultsProps> = ({ fileId, onProceedToCompliance }) => {
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [qualityScore, setQualityScore] = useState<DataQualityScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIssues, setSelectedIssues] = useState<number[]>([]);
  const [isValidating, setIsValidating] = useState(false);

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

  if (loading) {
    return (
      <div className="loading">
        {isValidating ? 'Running validation...' : 'Loading validation results...'}
      </div>
    );
  }

  return (
    <div className="validation-results">
      <div className="quality-score-section">
        {qualityScore && (
          <div className="quality-score">
            <h3>Data Quality Score: {qualityScore.overall.toFixed(1)}%</h3>
            <div className="score-details">
              <div>Completeness: {qualityScore.completeness.toFixed(1)}%</div>
              <div>Consistency: {qualityScore.consistency.toFixed(1)}%</div>
              <div>Accuracy: {qualityScore.accuracy.toFixed(1)}%</div>
            </div>
          </div>
        )}
      </div>

      <div className="issues-section">
        <h3>Validation Issues</h3>
        {error && (
          <div className="error-message" style={{ margin: '0 20px' }}>
            {error}
          </div>
        )}

        <div className="issues-list">
          {issues.map(issue => (
            <div key={issue.id} className={`issue-item ${issue.issue_type}`}>
              <div className="issue-header">
                <h4>{issue.title}</h4>
                <span className="severity">{issue.severity}</span>
              </div>
              <p className="description">{issue.description}</p>
              {issue.suggested_action && (
                <p className="suggested-action">Suggested Action: {issue.suggested_action}</p>
              )}
              {issue.auto_fixable && !issue.is_resolved && (
                <button
                  onClick={() => setSelectedIssues([...selectedIssues, issue.id])}
                  disabled={selectedIssues.includes(issue.id)}
                >
                  Auto-fix
                </button>
              )}
            </div>
          ))}
        </div>

        {selectedIssues.length > 0 && (
          <button onClick={handleAutoFix} className="auto-fix-all">
            Auto-fix Selected Issues ({selectedIssues.length})
          </button>
        )}

        <button
          className={`btn ${canProceedToCompliance ? 'btn-primary' : 'btn-disabled'}`}
          onClick={onProceedToCompliance}
          disabled={!canProceedToCompliance}
        >
          {canProceedToCompliance ? 'Proceed to Compliance Testing →' : 'Fix Critical Issues First'}
        </button>
      </div>
    </div>
  );
};

// Additional CSS classes needed (add to your App.css)
const additionalStyles = `
.validation-results-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.validation-header {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.validation-main-content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 24px;
}

.issues-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.validation-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.quality-score {
  text-align: center;
  margin: 20px 0;
}

.score-circle {
  display: inline-flex;
  align-items: baseline;
  justify-content: center;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 8px solid #e2e8f0;
  margin-bottom: 16px;
  position: relative;
}

.score-number {
  font-size: 36px;
  font-weight: 700;
  color: #3b82f6;
}

.score-suffix {
  font-size: 18px;
  font-weight: 600;
  color: #64748b;
}

.score-breakdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.score-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #64748b;
}

.next-steps.ready {
  background: #f0fdf4;
  border: 1px solid #10b981;
}

.next-steps.blocked {
  background: #fef2f2;
  border: 1px solid #ef4444;
}

.validation-footer {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-top: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.btn-disabled {
  background: #94a3b8;
  color: white;
  cursor: not-allowed;
}

.btn-disabled:hover {
  background: #94a3b8;
}

.issue-action {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
  font-size: 14px;
  color: #475569;
}

@media (max-width: 1024px) {
  .validation-main-content {
    grid-template-columns: 1fr;
  }
  
  .validation-sidebar {
    order: -1;
  }
}
`;

export default ValidationResults;