// Mirrors the backend Pydantic schemas so the frontend and API stay in sync.

export type UserRole = "owner" | "admin" | "member";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: UserRole;
  workspace_id: string;
  is_active: boolean;
  is_verified: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
  workspace_name: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export type DocumentSourceType =
  | "file_pdf"
  | "file_docx"
  | "file_txt"
  | "file_csv"
  | "file_xlsx"
  | "url"
  | "raw_text";

export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface DocumentOut {
  id: string;
  title: string;
  source_type: DocumentSourceType;
  source_uri: string | null;
  status: DocumentStatus;
  file_size_bytes: number | null;
  num_chunks: number | null;
  error_message: string | null;
  task_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  document_id: string;
  document_title: string;
  chunk_id: string;
  chunk_index: number;
  snippet: string;
  score: number;
}

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessageOut {
  id: string;
  role: MessageRole;
  content: string;
  citations: Citation[] | null;
  created_at: string;
}

export interface ChatSessionOut {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetailOut extends ChatSessionOut {
  messages: ChatMessageOut[];
}

export interface ChatQueryRequest {
  message: string;
  session_id?: string;
  document_ids?: string[];
  top_k?: number;
}

export interface ChatQueryResponse {
  session_id: string;
  message_id: string;
  answer: string;
  citations: Citation[];
  used_cache: boolean;
}
