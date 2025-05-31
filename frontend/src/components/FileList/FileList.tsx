import React, { useEffect, useState } from 'react';
import { getUploads } from '../../api/files';
import { FileUpload } from '../../types/files';
import './FileList.css';

export const FileList: React.FC = () => {
  const [files, setFiles] = useState<FileUpload[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const uploadedFiles = await getUploads();
      setFiles(uploadedFiles);
      setError(null);
    } catch (err) {
      setError('Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatFileSize = (bytes: number | null) => {
    if (bytes === null) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Byte';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)).toString());
    return Math.round((bytes / Math.pow(1024, i))) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="file-list-loading">
        <div className="spinner"></div>
        <p>Loading files...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="file-list-error">
        <p>{error}</p>
        <button onClick={loadFiles}>Retry</button>
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <div className="file-list-empty">
        <p>No files uploaded yet</p>
      </div>
    );
  }

  return (
    <div className="file-list">
      <h2>Uploaded Files</h2>
      <div className="file-list-grid">
        <div className="file-list-header">
          <div>Filename</div>
          <div>Size</div>
          <div>Type</div>
          <div>Uploaded</div>
          <div>Status</div>
        </div>
        {files.map((file) => (
          <div key={file.id} className="file-list-item">
            <div className="filename">{file.original_filename}</div>
            <div>{formatFileSize(file.file_size)}</div>
            <div>{file.mime_type || 'N/A'}</div>
            <div>{formatDate(file.uploaded_at)}</div>
            <div className={`status status-${file.status.toLowerCase()}`}>
              {file.status}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}; 