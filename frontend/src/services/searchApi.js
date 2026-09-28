import { api } from "./httpClient";

export const globalSearch = (q) =>
  api.get("/search", { params: { q } });
