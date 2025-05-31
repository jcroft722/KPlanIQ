import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileUploadError } from '../../types/files';
import './FileUpload.css';

interface FileUploadProps {
  onFileUpload: (file: File) => Promise<void>;
  onUploadError?: (error: FileUploadError) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload, onUploadError }) => {
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      try {
        await onFileUpload(acceptedFiles[0]);
      } catch (error: any) {
        onUploadError?.(error.response?.data || { detail: 'Upload failed' });
      }
    }
  }, [onFileUpload, onUploadError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    multiple: false
  });

  return (
    <div className="file-upload">
      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop the file here ...</p>
        ) : (
          <p>Drag and drop a file here, or click to select a file</p>
        )}
        <p className="file-types">Accepted file types: .csv, .xlsx, .xls</p>
      </div>
    </div>
  );
}; 