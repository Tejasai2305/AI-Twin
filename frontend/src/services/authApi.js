import { api, setToken, getToken } from "./httpClient";

export const signup = (username, password, email) =>
  api.post("/auth/signup", { username, password, email });

export const login = (username, password) =>
  api.post("/auth/login", { username, password });

export const requestPasswordReset = (email) =>
  api.post("/auth/forgot-password", { email });

export const resetPassword = (token, newPassword) =>
  api.post("/auth/reset-password", { token, new_password: newPassword });

export const getMe = () => api.get("/auth/me");

export const logout = () => setToken(null);

export const isLoggedIn = () => Boolean(getToken());

export { setToken };
