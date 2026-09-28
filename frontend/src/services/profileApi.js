import { api } from "./httpClient";

export const getProfile = () => api.get("/profile");
