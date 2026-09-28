import { api } from "./httpClient";

export const getGraph = (includeInactive = false) =>
  api.get("/graph", { params: { include_inactive: includeInactive } });

export const getGraphSummary = () =>
  api.get("/graph/summary");

export const getGraphNode = (nodeId) =>
  api.get(`/graph/node/${nodeId}`);
