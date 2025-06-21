import React, { useState, useEffect } from 'react';
import './FixIssues.css';
import { 
  getValidationResults, 
  applyIssueFix, 
  applyBulkFixes,
  updateIssueStatus
} from '../../services/api';
import { getDataQualityScore } from '../../api/files';
import IssueCard from './IssueCard';

// Types matching the backend ValidationEngine
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

interface FixOption {
  id: string;
  title: string;
  description: string;
  action_type: 'auto_fix' | 'manual_entry' | 'exclude' | 'accept' | 'generate_test';
  preview?: any;
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

interface FixIssuesProps {
  fileId: number;
  onComplete: () => void;
  onBack: () => void;
}

export const FixIssues: React.FC<FixIssuesProps> = ({ fileId, onComplete, onBack }) => {
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [filteredIssues, setFilteredIssues] = useState<ValidationIssue[]>([]);
  const [qualityScore, setQualityScore] = useState<DataQualityScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  
  // Filter states
  const [filters, setFilters] = useState({
    critical: true,
    warning: true,
    info: true,
    pending: true,
    fixed: false
  });
  
  // Expanded issues for showing fix interfaces
  const [expandedIssues, setExpandedIssues] = useState<Set<number>>(new Set());
  
  // Manual fix data
  const [manualFixData, setManualFixData] = useState<{[key: string]: any}>({});

  useEffect(() => {
    loadIssues();
  }, [fileId]);

  useEffect(() => {
    applyFilters();
  }, [issues, filters]);

  const loadIssues = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [validationData, qualityData] = await Promise.all([
        getValidationResults(fileId),
        getDataQualityScore(fileId).catch(() => null)
      ]);
      
      if (validationData && validationData.issues) {
        setIssues(validationData.issues);
      }
      
      setQualityScore(qualityData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load issues');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    const filtered = issues.filter(issue => {
      // Filter by type
      const typeMatch = (
        (filters.critical && issue.issue_type === 'critical') ||
        (filters.warning && issue.issue_type === 'warning') ||
        (filters.info && issue.issue_type === 'info')
      );
      
      // Filter by status
      const statusMatch = (
        (filters.pending && !issue.is_resolved) ||
        (filters.fixed && issue.is_resolved)
      );
      
      return typeMatch && statusMatch;
    });
    
    setFilteredIssues(filtered);
  };

  const handleFilterChange = (filterName: string, value: boolean) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  const handleAutoFix = async (issueId: number) => {
    try {
      setSaving(true);
      await applyIssueFix(fileId, issueId, { action_type: 'auto_fix' });
      
      // Update local state
      setIssues(prev => prev.map(issue => 
        issue.id === issueId 
          ? { ...issue, is_resolved: true }
          : issue
      ));
      
      setExpandedIssues(prev => {
        const newSet = new Set(prev);
        newSet.delete(issueId);
        return newSet;
      });
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply auto-fix');
    } finally {
      setSaving(false);
    }
  };

  const handleManualFix = async (issueId: number, fixData: any) => {
    try {
      setSaving(true);
      await applyIssueFix(fileId, issueId, {
        action_type: 'manual_entry',
        fix_data: fixData
      });
      
      // Update local state
      setIssues(prev => prev.map(issue => 
        issue.id === issueId 
          ? { ...issue, is_resolved: true }
          : issue
      ));
      
      setExpandedIssues(prev => {
        const newSet = new Set(prev);
        newSet.delete(issueId);
        return newSet;
      });
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply manual fix');
    } finally {
      setSaving(false);
    }
  };

  const handleAcceptIssue = async (issueId: number) => {
    try {
      setSaving(true);
      await updateIssueStatus(fileId, issueId, 'accepted');
      
      setIssues(prev => prev.map(issue => 
        issue.id === issueId 
          ? { ...issue, is_resolved: true }
          : issue
      ));
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to accept issue');
    } finally {
      setSaving(false);
    }
  };

  const handleAutoFixAll = async () => {
    try {
      setSaving(true);
      const autoFixableIssues = issues
        .filter(issue => issue.auto_fixable && !issue.is_resolved)
        .map(issue => issue.id);
      
      if (autoFixableIssues.length > 0) {
        await applyBulkFixes(fileId, autoFixableIssues);
        
        setIssues(prev => prev.map(issue => 
          autoFixableIssues.includes(issue.id)
            ? { ...issue, is_resolved: true }
            : issue
        ));
        
        setExpandedIssues(new Set());
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply bulk fixes');
    } finally {
      setSaving(false);
    }
  };

  const toggleIssueExpansion = (issueId: number) => {
    setExpandedIssues(prev => {
      const newSet = new Set(prev);
      if (newSet.has(issueId)) {
        newSet.delete(issueId);
      } else {
        newSet.add(issueId);
      }
      return newSet;
    });
  };

  const updateManualFixData = (issueId: number, field: string, value: any) => {
    setManualFixData(prev => ({
      ...prev,
      [issueId]: {
        ...prev[issueId],
        [field]: value
      }
    }));
  };

  const canComplete = () => {
    const criticalIssues = issues.filter(issue => 
      issue.issue_type === 'critical' && !issue.is_resolved
    );
    return criticalIssues.length === 0;
  };

  const getIssueCounts = () => {
    const critical = issues.filter(issue => issue.issue_type === 'critical').length;
    const warning = issues.filter(issue => issue.issue_type === 'warning').length;
    const info = issues.filter(issue => issue.issue_type === 'info').length;
    const pending = issues.filter(issue => !issue.is_resolved).length;
    const fixed = issues.filter(issue => issue.is_resolved).length;
    
    return { critical, warning, info, pending, fixed };
  };

  const remainingIssues = issues.filter(issue => !issue.is_resolved).length;
  const counts = getIssueCounts();

  if (loading) {
    return (
      <div className="fix-issues-loading">
        <div className="loading-spinner"></div>
        <p>Loading issues...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fix-issues-error">
        <h3>Error Loading Issues</h3>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={loadIssues}>
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="fix-issues-container">
      {/* Header */}
      <div className="header">
        <div className="breadcrumb">
          <button className="breadcrumb-link" onClick={onBack}>
            ← Validation Results
          </button>
          <span>/</span>
          <span>Fix Data Issues</span>
        </div>
        
        <div className="header-content">
          <div className="header-left">
            <h1>Fix Data Issues</h1>
            <div className="header-subtitle">
              Fix issues directly below - changes are applied immediately
            </div>
          </div>
          
          <div className="header-actions">
            <button 
              className="btn btn-secondary" 
              onClick={() => console.log('Save progress')}
              disabled={saving}
            >
              💾 Save Progress
            </button>
            <button 
              className={`btn ${canComplete() ? 'btn-success' : 'btn-secondary'}`}
              onClick={onComplete}
              disabled={!canComplete() || saving}
            >
              {canComplete() ? '✅ Complete & Test' : '⏳ Fix Critical Issues First'}
            </button>
          </div>
        </div>
      </div>

      <div className="main-content">
        {/* Filters */}
        <div className="sidebar">
          <div className="sidebar-left">
            <h3>Filter Issues</h3>
            
            <div className="filter-group">
              <label className="filter-label">Type</label>
              <div className="filter-options">
                <div className="filter-option">
                  <input 
                    type="checkbox" 
                    id="critical" 
                    checked={filters.critical}
                    onChange={(e) => handleFilterChange('critical', e.target.checked)}
                  />
                  <label htmlFor="critical">
                    <span className="severity-critical">●</span>
                    Critical
                    <span className="count-badge">{counts.critical}</span>
                  </label>
                </div>
                <div className="filter-option">
                  <input 
                    type="checkbox" 
                    id="warning" 
                    checked={filters.warning}
                    onChange={(e) => handleFilterChange('warning', e.target.checked)}
                  />
                  <label htmlFor="warning">
                    <span className="severity-warning">●</span>
                    Warning
                    <span className="count-badge">{counts.warning}</span>
                  </label>
                </div>
                <div className="filter-option">
                  <input 
                    type="checkbox" 
                    id="info" 
                    checked={filters.info}
                    onChange={(e) => handleFilterChange('info', e.target.checked)}
                  />
                  <label htmlFor="info">
                    <span className="severity-info">●</span>
                    Info
                    <span className="count-badge">{counts.info}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
          
          <div className="sidebar-right">
            <div className="filter-group">
              <label className="filter-label">Status</label>
              <div className="filter-options">
                <div className="filter-option">
                  <input 
                    type="checkbox" 
                    id="pending" 
                    checked={filters.pending}
                    onChange={(e) => handleFilterChange('pending', e.target.checked)}
                  />
                  <label htmlFor="pending">
                    Needs Fix 
                    <span className="count-badge">{counts.pending}</span>
                  </label>
                </div>
                <div className="filter-option">
                  <input 
                    type="checkbox" 
                    id="fixed" 
                    checked={filters.fixed}
                    onChange={(e) => handleFilterChange('fixed', e.target.checked)}
                  />
                  <label htmlFor="fixed">
                    Fixed 
                    <span className="count-badge">{counts.fixed}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Issues Panel */}
        <div className="issues-panel">
          <div className="panel-header">
            <div className="panel-title">Fix Issues ({remainingIssues} remaining)</div>
            <div className="bulk-actions">
              <button 
                className="btn btn-sm btn-primary" 
                onClick={handleAutoFixAll}
                disabled={saving || issues.filter(i => i.auto_fixable && !i.is_resolved).length === 0}
              >
                🔧 Auto-Fix All Possible
              </button>
            </div>
          </div>
          
          <div className="issues-list">
            {filteredIssues.map(issue => (
              <IssueCard
                key={issue.id}
                issue={issue}
                isExpanded={expandedIssues.has(issue.id)}
                onToggleExpansion={() => toggleIssueExpansion(issue.id)}
                onAutoFix={() => handleAutoFix(issue.id)}
                onManualFix={(fixData) => handleManualFix(issue.id, fixData)}
                onAccept={() => handleAcceptIssue(issue.id)}
                manualFixData={manualFixData[issue.id] || {}}
                onUpdateManualFixData={(field, value) => updateManualFixData(issue.id, field, value)}
                saving={saving}
              />
            ))}
            
            {filteredIssues.length === 0 && (
              <div className="empty-state">
                <div className="empty-state-icon">✅</div>
                <h3>No Issues Found</h3>
                <p>All issues matching your filters have been resolved.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FixIssues;