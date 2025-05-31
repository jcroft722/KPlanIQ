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
  const response = await api.put<FileUpload>(`/files/uploads/${fileId}/mappings`, { mappings });
  return response.data;
};

export const processFile = async (fileId: number): Promise<FileUpload> => {
  const response = await api.post<FileUpload>(`/files/uploads/${fileId}/process`);
  return response.data;
};

export const getFileMappings = async (fileId: number) => {
    const response = await axios.get(`${API_BASE_URL}/files/${fileId}/mappings`);
    return response.data;
};

// New portion for Compliance Tests

export const runComplianceTests = async (fileId: number) => {
    const response = await axios.post(`${API_BASE_URL}/files/${fileId}/compliance-test`);
    return response.data;
};

export const getComplianceHistory = async () => {
    const response = await axios.get(`${API_BASE_URL}/files/compliance-history`);
    return response.data;
};

export const getComplianceResults = async () => {
    const response = await axios.get(`${API_BASE_URL}/files/compliance-results`);
    return response.data;
};