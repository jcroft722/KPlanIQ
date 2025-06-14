import axios from 'axios';
import { FileUpload } from '../types/files';

const API_BASE_URL = 'http://localhost:8000';

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

// Add these functions to your frontend/src/services/api.ts

export const getComplianceResults = async () => {
  const response = await fetch(`${API_BASE_URL}/compliance/results`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch compliance results');
  }

  return response.json();
};

export const getComplianceHistory = async () => {
  const response = await fetch(`${API_BASE_URL}/compliance/history`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch compliance history');
  }

  return response.json();
};

export const runComplianceTests = async (fileId: number) => {
  const response = await fetch(`${API_BASE_URL}/files/${fileId}/compliance-test`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to run compliance tests');
  }

  return response.json();
};

export const runDataValidation = async (fileId: number) => {
  const response = await api.post(`/files/${fileId}/validate`);
  return response.data;
};

export const getValidationResults = async (fileId: number) => {
  const response = await api.get(`/files/${fileId}/validation-results`);
  return response.data;
};

export const autoFixIssues = async (fileId: number, issueIds?: number[]) => {
  const response = await api.post(`/files/${fileId}/auto-fix`, { 
    issue_ids: issueIds 
  });
  return response.data;
};

export const getDataQualityScore = async (fileId: number) => {
  const response = await api.get(`/files/${fileId}/data-quality-score`);
  return response.data;
};