import React, { useState, useEffect } from 'react';
import { uploadFile, updateFileMappings, processFile, getUploads, getComplianceResults } from './services/api';
import { FileUpload as FileUploadType, ColumnMapping } from './types/files';
import { FileUpload } from './components/FileUpload/FileUpload';
import { FileUploadError } from './types/files';
import ColumnMapper from './components/ColumnMapper';
import Dashboard from './components/Dashboard';
import { ComplianceTestingWorkflow } from './components/ComplianceTestingWorkflow';
import ValidationResults from './components/ValidationResults';
import './App.css';

interface DataIssue {
  row: number;
  column: string;
  issue: string;
  value: any;
}

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

interface ComplianceTestRun {
  id: number;
  file_id: number;
  file_name: string;
  run_date: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  results: ComplianceTestResult[];
}

type TabType = 'dashboard' | 'upload' | 'compliance';

const App: React.FC = () => {
  // Navigation state
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  
  // Upload workflow state
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [uploadedFile, setUploadedFile] = useState<FileUploadType | null>(null);
  const [columnMappings, setColumnMappings] = useState<{ [key: string]: ColumnMapping }>({});
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  // Dashboard state
  const [uploadedFiles, setUploadedFiles] = useState<FileUploadType[]>([]);
  const [recentComplianceResults, setRecentComplianceResults] = useState<ComplianceTestRun[]>([]);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState<boolean>(true);

  // Target schema for employee payroll data
  const targetSchema = [
    'SSN',
    'EEID',
    'FirstName',
    'LastName',
    'DOB',
    'DOH',
    'DOT',
    'HoursWorked',
    '%Ownership',
    'Officer',
    'PiorYearComp',
    'EmployeeDeferrals',
    'EmployerMatch',
    'EmployerProfitSharing',
    'EmployerSHContribuion'
  ];

  // Load dashboard data
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoadingDashboard(true);
    try {
      const [filesResponse, complianceResponse] = await Promise.all([
        getUploads(),
        getComplianceResults()
      ]);
      
      setUploadedFiles(filesResponse || []);
      setRecentComplianceResults(complianceResponse.recent_results || []);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    } finally {
      setIsLoadingDashboard(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    setError(null);
    try {
        const uploadResult = await uploadFile(file);
        console.log('Upload result:', uploadResult);
        setUploadedFile(uploadResult);
        setColumnMappings(uploadResult.suggested_mappings || {});
        
        // Process the file immediately after upload
        await processFile(uploadResult.id);
        
        setCurrentStep(2);
    } catch (err) {
        console.error('Error uploading file:', err);
        setError('Failed to upload file');
    } finally {
        setIsUploading(false);
    }
  };

  const handleUploadError = (error: FileUploadError) => {
    setError(error.detail);
    setIsUploading(false);
  };

  const handleUpdateMapping = async (sourceColumn: string, targetColumn: string | null) => {
    if (!uploadedFile) return;

    try {
        const updatedMappings = { ...columnMappings };
        
        if (targetColumn) {
            updatedMappings[sourceColumn] = {
                source_column: sourceColumn,
                target_column: targetColumn
            };
        } else {
            delete updatedMappings[sourceColumn];
        }

        await updateFileMappings(uploadedFile.id, updatedMappings);
        setColumnMappings(updatedMappings);
    } catch (err) {
        console.error('Error updating mapping:', err);
        setError('Failed to update column mapping');
    }
  };

  const handleNext = async () => {
    if (currentStep === 2 && uploadedFile) {
      setIsProcessing(true);
      setError(null);
      try {
        await processFile(uploadedFile.id);
        setCurrentStep(prev => prev + 1);
      } catch (err) {
        console.error('Processing error:', err);
        setError('Failed to process file. Please check your column mappings and try again.');
      } finally {
        setIsProcessing(false);
      }
    } else {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setCurrentStep(prev => prev - 1);
  };

  const handleUploadComplete = () => {
    // Refresh dashboard data
    loadDashboardData();
    
    // Switch to compliance testing tab
    setActiveTab('compliance');
    
    // Reset upload workflow
    setCurrentStep(1);
    setUploadedFile(null);
    setColumnMappings({});
    setError(null);
  };

  const handleComplianceComplete = () => {
    // Refresh dashboard data
    loadDashboardData();
    
    // Switch back to dashboard
    setActiveTab('dashboard');
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <Dashboard
            uploadedFiles={uploadedFiles}
            recentComplianceResults={recentComplianceResults}
            isLoading={isLoadingDashboard}
            onNavigateToUpload={() => setActiveTab('upload')}
            onNavigateToCompliance={() => setActiveTab('compliance')}
            onRefresh={loadDashboardData}
          />
        );

      case 'upload':
        return (
          <div className="upload-workflow">
            <div className="progress-steps">
              {[
                { number: 1, title: 'Upload File' },
                { number: 2, title: 'Map Columns' },
                { number: 3, title: 'Validate Data' },
                { number: 4, title: 'Complete' }
              ].map((step) => (
                <div key={step.number} className={`step ${
                  currentStep > step.number ? 'completed' : 
                  currentStep === step.number ? 'active' : 'inactive'
                }`}>
                  <div className="step-number">
                    {currentStep > step.number ? '✓' : step.number}
                  </div>
                  <div className="step-title">{step.title}</div>
                </div>
              ))}
            </div>

            {currentStep === 1 && (
              <div className="upload-section">
                <FileUpload 
                  onFileUpload={handleFileUpload}
                  onUploadError={handleUploadError}
                />
                {error && <div className="error-message">{error}</div>}
                {isUploading && <div className="loading">Uploading file...</div>}
              </div>
            )}

            {currentStep === 2 && uploadedFile && (
              <div className="mapping-section">
                <ColumnMapper
                  sourceColumns={uploadedFile.headers|| []}
                  targetSchema={targetSchema}
                  mappings={columnMappings}
                  onUpdateMapping={handleUpdateMapping}
                />
                <div className="navigation-buttons">
                  <button className="btn btn-secondary" onClick={handleBack}>
                    Back
                  </button>
                  <button 
                    className="btn btn-primary"
                    onClick={handleNext}
                  >
                    Next
                  </button>
                </div>
                <div className="mapping-info">
                  <p className="info-text">
                    Unmapped columns will be imported with null values. You can map them later if needed.
                  </p>
                </div>
              </div>
            )}

            {currentStep === 3 && uploadedFile && (
              <ValidationResults
                fileId={uploadedFile.id}
                onProceedToCompliance={() => {
                  setActiveTab('compliance');
                  setCurrentStep(1);
                }}
              />
            )}

            {currentStep === 4 && uploadedFile && (
              <div className="completion-section">
                <h2>Upload Complete!</h2>
                <div className="completion-content">
                  <p>Your file has been successfully processed and is ready for compliance testing.</p>
                  <div className="file-summary">
                    <p>File: {uploadedFile.original_filename}</p>
                    <p>Rows Processed: {uploadedFile.row_count}</p>
                    <p>Status: {uploadedFile.status}</p>
                  </div>
                </div>
                <div className="navigation-buttons">
                  <button className="btn btn-secondary" onClick={handleBack}>
                    Back
                  </button>
                  <button 
                    className="btn btn-primary"
                    onClick={handleUploadComplete}
                  >
                    Go to Compliance Testing
                  </button>
                </div>
              </div>
            )}
          </div>
        );

      case 'compliance':
        return (
          <ComplianceTestingWorkflow
            availableFiles={uploadedFiles}
            onComplete={handleComplianceComplete}
            onRefreshDashboard={loadDashboardData}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>401k Data Processor</h1>
          <nav className="tab-navigation">
            <button 
              className={`tab-button ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              📊 Dashboard
            </button>
            <button 
              className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => setActiveTab('upload')}
            >
              📁 Data Upload
            </button>
            <button 
              className={`tab-button ${activeTab === 'compliance' ? 'active' : ''}`}
              onClick={() => setActiveTab('compliance')}
            >
              ✅ Compliance Testing
            </button>
          </nav>
        </div>
      </header>
      <main>
        {renderTabContent()}
      </main>
    </div>
  );
};

export default App;