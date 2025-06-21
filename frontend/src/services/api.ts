import axios from 'axios';
import { FileUpload, ColumnMapping } from '../types/files';


// const API_BASE_URL = 'http://localhost:8000/api';
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const apiRequest = async (url: string, options: RequestInit = {}) => {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const uploadFile = async (file: File): Promise<FileUpload> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post<FileUpload>('/api/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const getUploads = async (): Promise<FileUpload[]> => {
  const response = await api.get<FileUpload[]>('/api/files/uploads');
  return response.data;
};

export const getUploadDetails = async (fileId: number): Promise<FileUpload> => {
  const response = await api.get<FileUpload>(`/api/files/uploads/${fileId}`);
  return response.data;
};

export const updateFileMappings = async (fileId: number, mappings: { [key: string]: ColumnMapping }): Promise<FileUpload> => {
  // Convert the mappings to the format expected by the backend
  const formattedMappings: { [key: string]: string } = {};
  Object.entries(mappings).forEach(([sourceCol, mapping]) => {
    if (mapping.target_column) {
      formattedMappings[sourceCol] = mapping.target_column;
    }
  });
  
  const response = await api.put<FileUpload>(`/api/files/${fileId}/mappings`, formattedMappings);
  return response.data;
};

export const processFile = async (fileId: number): Promise<FileUpload> => {
  const response = await api.post<FileUpload>(`/api/files/${fileId}/process`);
  return response.data;
};

export const getFileMappings = async (fileId: number) => {
  const response = await api.get(`/api/files/${fileId}/mappings`);
  return response.data;
};

// New portion for Compliance Tests

export const runComplianceTests = async (fileId: number) => {
    const response = await axios.post(`${API_BASE_URL}/api/files/${fileId}/compliance-test`);
    return response.data;
};

export const getComplianceHistory = async () => {
  const response = await api.get('/api/compliance/history');
  return response.data;
};

export const getComplianceResults = async () => {
  const response = await api.get('/api/compliance/results');
  return response.data;
};

// Validation API functions
export const getValidationResults = async (fileId: number) => {
  const response = await axios.get(`${API_BASE_URL}/api/files/${fileId}/validation-results`);
  return response.data;
};

export const autoFixIssues = async (fileId: number, issueIds: number[]) => {
  const response = await axios.post(`${API_BASE_URL}/api/files/${fileId}/auto-fix`, {
    issue_ids: issueIds
  });
  return response.data;
};
// Apply a fix to a specific issue
export const applyIssueFix = async (
  fileId: number, 
  issueId: number, 
  fixData: {
    action_type: 'auto_fix' | 'manual_entry' | 'exclude' | 'accept' | 'generate_test';
    fix_data?: any;
  }
) => {
  return apiRequest(`/api/files/${fileId}/issues/${issueId}/fix`, {
    method: 'POST',
    body: JSON.stringify(fixData),
  });
};

// Apply bulk fixes to multiple issues
export const applyBulkFixes = async (fileId: number, issueIds: number[]) => {
  return apiRequest(`/api/files/${fileId}/issues/bulk-fix`, {
    method: 'POST',
    body: JSON.stringify({ issue_ids: issueIds }),
  });
};

// Update issue status (accept, reject, etc.)
export const updateIssueStatus = async (
  fileId: number, 
  issueId: number, 
  status: 'accepted' | 'rejected' | 'excluded'
) => {
  return apiRequest(`/api/files/${fileId}/issues/${issueId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
};

// Get fix suggestions for an issue
export const getFixSuggestions = async (fileId: number, issueId: number) => {
  return apiRequest(`/api/files/${fileId}/issues/${issueId}/suggestions`);
};

// Preview auto-fix changes before applying
export const previewAutoFix = async (fileId: number, issueId: number) => {
  return apiRequest(`/api/files/${fileId}/issues/${issueId}/preview-fix`);
};

// Save fix progress
export const saveFixProgress = async (fileId: number) => {
  return apiRequest(`/api/files/${fileId}/fix-progress`, {
    method: 'POST',
  });
};

// Get current fix progress
export const getFixProgress = async (fileId: number) => {
  return apiRequest(`/api/files/${fileId}/fix-progress`);
};

// Validate manual fix data before applying
export const validateManualFix = async (
  fileId: number, 
  issueId: number, 
  fixData: any
) => {
  return apiRequest(`/api/files/${fileId}/issues/${issueId}/validate-fix`, {
    method: 'POST',
    body: JSON.stringify(fixData),
  });
};

// Export updated file after fixes
export const exportFixedFile = async (fileId: number, format: 'xlsx' | 'csv' = 'xlsx') => {
  const response = await fetch(`${API_BASE_URL}/api/files/${fileId}/export?format=${format}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`, // Adjust based on your auth
    },
  });

  if (!response.ok) {
    throw new Error('Failed to export fixed file');
  }

  // Return blob for download
  return response.blob();
};

// Get issue fix history
export const getIssueFixHistory = async (fileId: number, issueId: number) => {
  return apiRequest(`/api/files/${fileId}/issues/${issueId}/history`);
};

// Undo a fix
export const undoIssueFix = async (fileId: number, issueId: number) => {
  return apiRequest(`/api/files/${fileId}/issues/${issueId}/undo`, {
    method: 'POST',
  });
};

// Check if file is ready for compliance testing after fixes
export const checkComplianceReadiness = async (fileId: number) => {
  return apiRequest(`/api/files/${fileId}/compliance-readiness`);
};