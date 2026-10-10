import { api } from "@/lib/api";
import type { ChatSessionOut, ChatSessionDetailOut, ChatQueryRequest, ChatQueryResponse } from "@/types";

export async function listSessions(): Promise<ChatSessionOut[]> {
  const { data } = await api.get<ChatSessionOut[]>("/chat/sessions");
  return data;
}

export async function createSession(): Promise<ChatSessionOut> {
  const { data } = await api.post<ChatSessionOut>("/chat/sessions");
  return data;
}

export async function getSessionDetail(sessionId: string): Promise<ChatSessionDetailOut> {
  const { data } = await api.get<ChatSessionDetailOut>(`/chat/sessions/${sessionId}`);
  return data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/chat/sessions/${sessionId}`);
}

export async function sendQuery(payload: ChatQueryRequest): Promise<ChatQueryResponse> {
  const { data } = await api.post<ChatQueryResponse>("/chat/query", payload);
  return data;
}
