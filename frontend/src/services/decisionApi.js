import { api } from "./httpClient";

export const compareOptions = (options, criteria, weights) =>
  api.post("/decision/compare", { options, criteria, weights });
