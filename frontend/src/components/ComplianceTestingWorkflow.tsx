import React, { useState, useEffect } from 'react';
import { runComplianceTests, getComplianceHistory } from '../services/api';
import { FileUpload } from '../types/files';
import { ComplianceTestRun } from '../types/compliance';


//interface FileUploadResponse {
//  id: number;
//  original_filename: string;
// filename: string;
//  size: number;
//  rows: number;
//  columns: number;
//  status: string;
//  created_at: string;
//}

interface ComplianceTestResult {
  id: number;
  file_id: number;
  test_name: string;
  test_category: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  affected_employees: number;
  details: any;
  created_at: string;
}

interface ComplianceTest {
  id: string;
  name: string;
  description: string;
  category: 'eligibility' | 'limits' | 'discrimination' | 'coverage';
  status: 'pending' | 'running' | 'passed' | 'failed' | 'warning';
  result?: {
    passed: boolean;
    message: string;
    details?: any;
    affectedEmployees?: number;
  };
}

interface ComplianceTestingWorkflowProps {
  availableFiles: FileUpload[];
  onComplete: () => void;
  onRefreshDashboard: () => void;
}

export const ComplianceTestingWorkflow: React.FC<ComplianceTestingWorkflowProps> = ({
  availableFiles,
  onComplete,
  onRefreshDashboard
}) => {
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [complianceTests, setComplianceTests] = useState<ComplianceTest[]>([]);
  const [isRunningTests, setIsRunningTests] = useState<boolean>(false);
  const [testHistory, setTestHistory] = useState<ComplianceTestRun[]>([]);
  const [selectedHistoryRun, setSelectedHistoryRun] = useState<ComplianceTestRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Available processed files (only processed ones)
  const processedFiles = availableFiles.filter(file => file.status === 'processed');

  // Initial compliance tests definition
  const initialComplianceTests: ComplianceTest[] = [
    {
      id: 'min_age',
      name: 'Minimum Age Requirement',
      description: 'Employees must be at least 21 years old to participate',
      category: 'eligibility',
      status: 'pending'
    },
    {
      id: 'service_requirement',
      name: 'Service Requirement',
      description: 'Employees must have 1 year of service (1,000 hours)',
      category: 'eligibility',
      status: 'pending'
    },
    {
      id: 'annual_compensation_limit',
      name: 'Annual Compensation Limit',
      description: 'Employee compensation cannot exceed annual IRS limit ($345,000 for 2024)',
      category: 'limits',
      status: 'pending'
    },
    {
      id: 'deferral_limit',
      name: 'Elective Deferral Limit',
      description: 'Employee deferrals cannot exceed annual limit ($23,500 for 2024)',
      category: 'limits',
      status: 'pending'
    },
    {
      id: 'catch_up_limit',
      name: 'Catch-up Contribution Limit',
      description: 'Employees 50+ can defer additional $7,500 (total $31,000 for 2024)',
      category: 'limits',
      status: 'pending'
    },
    {
      id: 'acp_test',
      name: 'ACP Nondiscrimination Test',
      description: 'Average contribution percentage test for matching contributions',
      category: 'discrimination',
      status: 'pending'
    },
    {
      id: 'adp_test',
      name: 'ADP Nondiscrimination Test',
      description: 'Average deferral percentage test for employee deferrals',
      category: 'discrimination',
      status: 'pending'
    },
    {
      id: 'top_heavy',
      name: 'Top Heavy Test',
      description: 'Key employee benefits cannot exceed 60% of total plan benefits',
      category: 'discrimination',
      status: 'pending'
    },
    {
      id: 'coverage_ratio',
      name: 'Coverage Ratio Test',
      description: 'Plan must benefit minimum percentage of non-highly compensated employees',
      category: 'coverage',
      status: 'pending'
    },
    {
      id: 'minimum_participation',
      name: 'Minimum Participation',
      description: 'Plan must cover minimum number or percentage of employees',
      category: 'coverage',
      status: 'pending'
    }
  ];

  useEffect(() => {
    loadTestHistory();
  }, []);

  useEffect(() => {
    if (selectedFileId) {
      setComplianceTests(initialComplianceTests);
    }
  }, [selectedFileId]);

  const loadTestHistory = async () => {
    try {
      const history = await getComplianceHistory();
      setTestHistory(history.test_runs || []);
    } catch (err) {
      console.error('Error loading test history:', err);
      setError('Failed to load test history');
    }
  };

  const runTests = async () => {
    if (!selectedFileId) return;

    setIsRunningTests(true);
    setError(null);

    try {
      const results = await runComplianceTests(selectedFileId);
      
      // Update test statuses based on results
      setComplianceTests(prev => prev.map(test => {
        const result = results.find((r: ComplianceTestResult) => r.test_name === test.name);
        if (result) {
          return {
            ...test,
            status: result.status,
            result: {
              passed: result.status === 'passed',
              message: result.message,
              details: result.details,
              affectedEmployees: result.affected_employees
            }
          };
        }
        return test;
      }));

      // Refresh test history and dashboard
      await loadTestHistory();
      onRefreshDashboard();

    } catch (err) {
      console.error('Error running compliance tests:', err);
      setError('Failed to run compliance tests');
    } finally {
      setIsRunningTests(false);
    }
  };

  const getTestStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return '✓';
      case 'failed': return '✗';
      case 'warning': return '⚠';
      case 'running': return '⟳';
      default: return '?';
    }
  };

  const getTestStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'warning': return 'text-yellow-600';
      case 'running': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '0 MB';
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const selectedFile = processedFiles.find(f => f.id === selectedFileId);
  const testsCompleted = complianceTests.every(test => test.status === 'passed' || test.status === 'failed');

  return (
    <div className="compliance-workflow">
      <div className="compliance-header">
        <h1>Compliance Testing</h1>
        <p className="subtitle">
          Run 401(k) compliance tests on your processed employee data files
        </p>
      </div>

      {/* File Selection */}
      <div className="file-selection-section">
        <h2>Select File for Testing</h2>
        {processedFiles.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📄</div>
            <h3>No processed files available</h3>
            <p>Upload and process employee data files before running compliance tests</p>
          </div>
        ) : (
          <div className="file-grid">
            {processedFiles.map((file) => (
              <div
                key={file.id}
                className={`file-card ${selectedFileId === file.id ? 'selected' : ''}`}
                onClick={() => setSelectedFileId(file.id)}
              >
                <div className="file-card-header">
                  <div className="file-icon">📄</div>
                  <div className="file-info">
                    <div className="file-name">{file.original_filename}</div>
                    <div className="file-details">
                      {formatFileSize(file.file_size)} • {file.row_count?.toLocaleString() || 0} rows
                    </div>
                  </div>
                </div>
                <div className="file-date">{formatDate(file.created_at)}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Compliance Tests */}
      {selectedFileId && (
        <div className="compliance-testing-section">
          <div className="section-header">
            <h2>Compliance Tests for {selectedFile?.original_filename}</h2>
            {!testsCompleted && !isRunningTests && (
              <button 
                className="btn btn-primary"
                onClick={runTests}
                disabled={isRunningTests}
              >
                Run All Tests
              </button>
            )}
          </div>

          {isRunningTests && (
            <div className="running-indicator">
              <span className="spinner">🔄</span>
              Running compliance tests... Please wait
            </div>
          )}

          {error && <div className="error-message">{error}</div>}

          <div className="compliance-categories">
            {['eligibility', 'limits', 'discrimination', 'coverage'].map(category => {
              const categoryTests = complianceTests.filter(test => test.category === category);
              const completedTests = categoryTests.filter(test => test.status === 'passed' || test.status === 'failed');
              const passedTests = categoryTests.filter(test => test.status === 'passed');
              
              return (
                <div key={category} className="compliance-category">
                  <div className="category-header">
                    <h3 className="category-title">
                      {category.charAt(0).toUpperCase() + category.slice(1)} Tests
                    </h3>
                    <div className="category-progress">
                      {completedTests.length}/{categoryTests.length} complete
                      {completedTests.length === categoryTests.length && (
                        <span className={`category-status ${passedTests.length === categoryTests.length ? 'passed' : 'failed'}`}>
                          {passedTests.length === categoryTests.length ? '✅' : '❌'}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="compliance-tests">
                    {categoryTests.map(test => (
                      <div key={test.id} className={`compliance-test test-${test.status}`}>
                        <div className="test-header">
                          <div className="test-info">
                            <span className="test-icon">{getTestStatusIcon(test.status)}</span>
                            <div>
                              <div className="test-name">{test.name}</div>
                              <div className="test-description">{test.description}</div>
                            </div>
                          </div>
                          <div className="test-status" style={{ color: getTestStatusColor(test.status) }}>
                            {test.status.charAt(0).toUpperCase() + test.status.slice(1)}
                          </div>
                        </div>
                        
                        {test.result && (
                          <div className="test-result">
                            <div className="result-message">{test.result.message}</div>
                            {test.result.affectedEmployees && test.result.affectedEmployees > 0 && (
                              <div className="affected-employees">
                                Affects {test.result.affectedEmployees} employee{test.result.affectedEmployees !== 1 ? 's' : ''}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {testsCompleted && (
            <div className="test-summary">
              <h3>Test Summary</h3>
              <div className="summary-stats">
                <div className="summary-stat passed">
                  <div className="stat-number">{complianceTests.filter(t => t.status === 'passed').length}</div>
                  <div className="stat-label">Passed</div>
                </div>
                <div className="summary-stat failed">
                  <div className="stat-number">{complianceTests.filter(t => t.status === 'failed').length}</div>
                  <div className="stat-label">Failed</div>
                </div>
                <div className="summary-stat total">
                  <div className="stat-number">{complianceTests.length}</div>
                  <div className="stat-label">Total</div>
                </div>
              </div>
              <div className="export-actions">
                <button className="btn btn-secondary">📄 Export PDF Report</button>
                <button className="btn btn-secondary">📊 Export Excel Summary</button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Test History */}
      <div className="test-history-section">
        <h2>Test History</h2>
        {testHistory.length === 0 ? (
          <div className="empty-state-small">
            <p>No test history available yet</p>
          </div>
        ) : (
          <div className="history-list">
            {testHistory.slice(0, 10).map((run) => (
              <div 
                key={run.id} 
                className={`history-item ${selectedHistoryRun?.id === run.id ? 'selected' : ''}`}
                onClick={() => setSelectedHistoryRun(selectedHistoryRun?.id === run.id ? null : run)}
              >
                <div className="history-info">
                  <div className="history-file">{run.file_name}</div>
                  <div className="history-details">
                    {formatDate(run.run_date)} • {run.passed_tests}/{run.total_tests} passed
                  </div>
                </div>
                <div className="history-status">
                  {run.failed_tests === 0 ? '✅' : '❌'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="navigation-buttons">
        <button className="btn btn-secondary" onClick={onComplete}>
          ← Back to Dashboard
        </button>
        {testsCompleted && (
          <button className="btn btn-primary" onClick={onComplete}>
            Done
          </button>
        )}
      </div>
    </div>
  );
};