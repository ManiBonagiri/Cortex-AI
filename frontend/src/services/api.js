import axios from "axios";

const BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

export const sendMessage = async (message, sessionId, chatHistory = []) => {
  const response = await api.post("/api/chat/query", {
    message,
    session_id: sessionId,
    chat_history: chatHistory,
  });
  return response.data;
};

export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${BASE_URL}/api/upload/csv`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const clearHistory = async (sessionId) => {
  const response = await api.delete("/api/chat/history", {
    params: { session_id: sessionId },
  });
  return response.data;
};

export const getChatHistory = async (sessionId) => {
  const response = await api.get("/api/chat/history", {
    params: { session_id: sessionId },
  });
  return response.data;
};

export const getUploadedFiles = async () => {
  const response = await api.get("/api/upload/files");
  return response.data;
};

export const clearUploadedFiles = async () => {
  const response = await api.delete("/api/upload/files");
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get("/api/chat/health");
  return response.data;
};