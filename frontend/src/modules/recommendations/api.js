import { apiGet } from "../../core/api/client";

export function fetchRecommendations() {
  return apiGet("/recommendations");
}