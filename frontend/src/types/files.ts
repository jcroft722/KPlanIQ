export interface FileUpload {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number | null;
  file_path: string | null;
  mime_type: string | null;
  row_count: number | null;
  column_count: number | null;
  headers: string[] | null;
  uploaded_at: string;
  created_at: string;
  status: string;
  suggested_mappings?: {
    [key: string]: ColumnMapping;
  };
}

export interface FileUploadError {
  detail: string;
}

export interface ColumnMapping {
  source_column: string;
  target_column: string | null;
}

export interface FileUploadResponse {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number | null;
  file_path: string | null;
  mime_type: string | null;
  row_count: number | null;
  column_count: number | null;
  headers: string[] | null;
  uploaded_at: string;
  created_at: string;
  status: string;
  suggested_mappings?: {
    [key: string]: ColumnMapping;
  };
} 