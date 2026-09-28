import { api, setToken, getToken } from "./httpClient";

export const signup = (username, password) =>
  api.post("/auth/signup", { username, password });

export const login = (username, password) =>
  api.post("/auth/login", { username, password });

export const getMe = () => api.get("/auth/me");

export const logout = () => setToken(null);

export const isLoggedIn = () => Boolean(getToken());

export { setToken };
