import { api } from "./httpClient";

export const getDocuments = (conversationId) =>
  api.get("/documents", { params: { conversation_id: conversationId || undefined } });

export const getDocument = (id) =>
  api.get(`/documents/${id}`);

export const deleteDocument = (id) =>
  api.delete(`/documents/${id}`);
