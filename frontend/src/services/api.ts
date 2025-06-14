import axios from 'axios';
import { FileUpload, ColumnMapping } from '../types/files';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const uploadFile = async (file: File): Promise<FileUpload> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post<FileUpload>('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const getUploads = async (): Promise<FileUpload[]> => {
  const response = await api.get<FileUpload[]>('/files/uploads');
  return response.data;
};

export const getUploadDetails = async (fileId: number): Promise<FileUpload> => {
  const response = await api.get<FileUpload>(`/files/uploads/${fileId}`);
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
  
  const response = await api.put<FileUpload>(`/files/${fileId}/mappings`, formattedMappings);
  return response.data;
};

export const processFile = async (fileId: number): Promise<FileUpload> => {
  const response = await api.post<FileUpload>(`/files/${fileId}/process`);
  return response.data;
};

export const getFileMappings = async (fileId: number) => {
  const response = await api.get(`/files/${fileId}/mappings`);
  return response.data;
};

// New portion for Compliance Tests

export const runComplianceTests = async (fileId: number) => {
    const response = await axios.post(`${API_BASE_URL}/files/${fileId}/compliance-test`);
    return response.data;
};

export const getComplianceHistory = async () => {
  const response = await api.get('/compliance/history');
  return response.data;
};

export const getComplianceResults = async () => {
  const response = await api.get('/compliance/results');
  return response.data;
};

// Validation API functions
export const getValidationResults = async (fileId: number) => {
  const response = await axios.get(`${API_BASE_URL}/files/${fileId}/validation-results`);
  return response.data;
};

export const autoFixIssues = async (fileId: number, issueIds: number[]) => {
  const response = await axios.post(`${API_BASE_URL}/files/${fileId}/auto-fix`, {
    issue_ids: issueIds
  });
  return response.data;
};

export const getDataQualityScore = async (fileId: number) => {
  const response = await axios.get(`${API_BASE_URL}/files/${fileId}/quality-score`);
  return response.data;
};