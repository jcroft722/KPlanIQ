import React, { useState, useEffect } from 'react';
import { getUploads } from '../services/api';
import { FileUpload } from '../types/files';
import './FileList.css';

export const FileList: React.FC = () => {
  const [files, setFiles] = useState<FileUpload[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileUpload | null>(null);

  useEffect(() => {
    const loadFiles = async () => {
      const data = await getUploads();
      setFiles(data);
    };
    loadFiles();
  }, []);

  const renderMappingSuggestions = (file: FileUpload) => {
    if (!file.suggested_mappings) return null;

    return (
      <div className="mapping-suggestions">
        <h4>Column Mappings</h4>
        <div className="mapping-grid">
          {Object.entries(file.suggested_mappings).map(([sourceCol, mapping]) => (
            <div key={sourceCol} className="mapping-row">
              <div className="source-column">{sourceCol}</div>
              {mapping.target_column ? (
                <>
                  <div className="mapping-arrow">→</div>
                  <div className="target-column">{mapping.target_column}</div>
                </>
              ) : (
                <div className="unmapped">Not mapped</div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="file-list">
      <h2>Uploaded Files</h2>
      <div className="files-grid">
        {files.map((file) => (
          <div
            key={file.id}
            className={`file-card ${selectedFile?.id === file.id ? 'selected' : ''}`}
            onClick={() => setSelectedFile(file)}
          >
            <div className="file-header">
              <h3>{file.original_filename}</h3>
              <span className={`status ${file.status}`}>{file.status}</span>
            </div>
            <div className="file-details">
              <p>Rows: {file.row_count}</p>
              <p>Columns: {file.column_count}</p>
              <p>Uploaded: {new Date(file.uploaded_at).toLocaleString()}</p>
            </div>
            {selectedFile?.id === file.id && renderMappingSuggestions(file)}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FileList; 