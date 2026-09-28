import { api } from "./httpClient";

export const getDashboard = () => api.get("/dashboard");
