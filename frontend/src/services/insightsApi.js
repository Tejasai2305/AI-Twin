import { api } from "./httpClient";

export const getInsights = () => api.get("/insights");
