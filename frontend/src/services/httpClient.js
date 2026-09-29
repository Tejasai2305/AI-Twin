import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
});

const TOKEN_KEY = "ai_twin_access_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const setToken = (token) => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
};

// Attaches the current token to every request made through this
// shared instance - every *Api.js file in this app imports `api`
// from here instead of creating its own axios.create(), so signing
// in once authenticates every page (Memory, Graph, Timeline,
// Profile, Documents, Search, Dashboard, Insights, Decisions, chat).
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

