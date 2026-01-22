/**
 * File metadata types
 */

export interface FileMetadataBase {
  filename: string;
  file_size: number;
  file_path: string;
  content_type?: string | null;
  file_hash?: string | null;
  parsed: boolean;
  parse_error?: string | null;
}

export interface FileMetadataCreate extends FileMetadataBase {
  session_id: string;
}

export interface FileMetadataUpdate {
  filename?: string;
  parsed?: boolean;
  parse_error?: string | null;
}

export interface FileMetadataPublic extends FileMetadataBase {
  id: string;
  session_id: string;
  user_id: string;
  create_time: string;
  update_time: string;
}

export interface FileMetadatasPublic {
  data: FileMetadataPublic[];
  count: number;
}

export interface FileUploadResponse {
  id: string;
  filename: string;
  file_size: number;
  message: string;
}
