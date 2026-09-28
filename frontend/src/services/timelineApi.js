import { api } from "./httpClient";

export const getTimeline = (year, category) =>
  api.get("/timeline", { params: { year: year || undefined, category: category || undefined } });

export const getTimelineYears = () =>
  api.get("/timeline/years");

export const getTimelineCategories = () =>
  api.get("/timeline/categories");
