import React from 'react';
import { FileUpload } from '../types/files';
import { ComplianceTestRun } from '../types/compliance';

//interface FileUploadResponse {
//  id: number;
//  original_filename: string;
//  filename: string;
// size: number;
//  rows: number;
//  columns: number;
//  status: string;
//  created_at: string;
//}

interface DashboardProps {
  uploadedFiles: FileUpload[];
  recentComplianceResults: ComplianceTestRun[];
  isLoading: boolean;
  onNavigateToUpload: () => void;
  onNavigateToCompliance: () => void;
  onRefresh: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({
  uploadedFiles,
  recentComplianceResults,
  isLoading,
  onNavigateToUpload,
  onNavigateToCompliance,
  onRefresh
}) => {
  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '0 MB';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
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

  const getComplianceStatusColor = (passed: number, total: number) => {
    const passRate = passed / total;
    if (passRate === 1) return '#10b981'; // green
    if (passRate >= 0.8) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  if (isLoading) {
    return (
      <div className="dashboard">
        <div className="loading-dashboard">
          <div className="loading">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p className="dashboard-subtitle">
          Monitor your data uploads and compliance testing results
        </p>
        <button className="btn btn-secondary refresh-btn" onClick={onRefresh}>
          🔄 Refresh
        </button>
      </div>

      {/* Quick Stats */}
      <div className="quick-stats">
        <div className="stat-card">
          <div className="stat-number">{uploadedFiles.length}</div>
          <div className="stat-label">Files Uploaded</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{recentComplianceResults.length}</div>
          <div className="stat-label">Compliance Tests</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">
            {uploadedFiles.filter(f => f.status === 'completed').length}
          </div>
          <div className="stat-label">Files Ready</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">
            {recentComplianceResults.filter(r => r.failed_tests === 0).length}
          </div>
          <div className="stat-label">Passed Tests</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="action-buttons">
          <button className="action-card" onClick={onNavigateToUpload}>
            <div className="action-icon">📁</div>
            <div className="action-title">Upload New File</div>
            <div className="action-description">
              Import and validate employee data
            </div>
          </button>
          <button className="action-card" onClick={onNavigateToCompliance}>
            <div className="action-icon">✅</div>
            <div className="action-title">Run Compliance Tests</div>
            <div className="action-description">
              Test uploaded files for 401(k) compliance
            </div>
          </button>
        </div>
      </div>

      <div className="dashboard-content">
        {/* Recent Files */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Recent Files</h2>
            <button className="btn btn-primary btn-sm" onClick={onNavigateToUpload}>
              + Upload New
            </button>
          </div>
          
          {uploadedFiles.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📄</div>
              <h3>No files uploaded yet</h3>
              <p>Get started by uploading your first employee data file</p>
              <button className="btn btn-primary" onClick={onNavigateToUpload}>
                Upload File
              </button>
            </div>
          ) : (
            <div className="files-list">
              {uploadedFiles.slice(0, 5).map((file) => (
                <div key={file.id} className="file-item">
                  <div className="file-info">
                    <div className="file-name">{file.original_filename}</div>
                    <div className="file-details">
                      {formatFileSize(file.file_size)} • {file.row_count?.toLocaleString() || 0} rows • {file.column_count || 0} columns
                    </div>
                    <div className="file-date">{formatDate(file.created_at)}</div>
                  </div>
                  <div className="file-status">
                    <span className={`status-badge status-${file.status}`}>
                      {file.status}
                    </span>
                  </div>
                </div>
              ))}
              {uploadedFiles.length > 5 && (
                <div className="view-all">
                  <button className="btn btn-secondary btn-sm">
                    View All {uploadedFiles.length} Files
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Recent Compliance Results */}
        <div className="dashboard-section">
          <div className="section-header">
            <h2>Recent Compliance Tests</h2>
            <button className="btn btn-primary btn-sm" onClick={onNavigateToCompliance}>
              Run New Test
            </button>
          </div>
          
          {recentComplianceResults.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">✅</div>
              <h3>No compliance tests run yet</h3>
              <p>Start testing your uploaded files for 401(k) compliance</p>
              <button className="btn btn-primary" onClick={onNavigateToCompliance}>
                Run Compliance Test
              </button>
            </div>
          ) : (
            <div className="compliance-list">
              {recentComplianceResults.slice(0, 5).map((result) => (
                <div key={result.id} className="compliance-item">
                  <div className="compliance-info">
                    <div className="compliance-file">{result.file_name}</div>
                    <div className="compliance-details">
                      {result.total_tests} tests • {formatDate(result.run_date)}
                    </div>
                  </div>
                  <div className="compliance-results">
                    <div 
                      className="test-summary"
                      style={{ 
                        color: getComplianceStatusColor(result.passed_tests, result.total_tests)
                      }}
                    >
                      {result.passed_tests}/{result.total_tests} passed
                    </div>
                    <div className="test-indicator">
                      {result.failed_tests === 0 ? '✅' : '❌'}
                    </div>
                  </div>
                </div>
              ))}
              {recentComplianceResults.length > 5 && (
                <div className="view-all">
                  <button className="btn btn-secondary btn-sm">
                    View All Test Results
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;