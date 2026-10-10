import { api } from "@/lib/api";
import type { DocumentOut } from "@/types";

export async function listDocuments(): Promise<DocumentOut[]> {
  const { data } = await api.get<DocumentOut[]>("/documents");
  return data;
}

export async function uploadDocument(file: File): Promise<DocumentOut> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<DocumentOut>("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function ingestUrl(url: string, title?: string): Promise<DocumentOut> {
  const { data } = await api.post<DocumentOut>("/documents/ingest-url", { url, title });
  return data;
}

export async function ingestText(title: string, content: string): Promise<DocumentOut> {
  const { data } = await api.post<DocumentOut>("/documents/ingest-text", { title, content });
  return data;
}

export async function getDocument(id: string): Promise<DocumentOut> {
  const { data } = await api.get<DocumentOut>(`/documents/${id}`);
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`);
}
