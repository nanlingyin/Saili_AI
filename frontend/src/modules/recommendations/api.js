import { apiGet } from "../../core/api/client";

export function fetchRecommendations() {
  return apiGet("/recommendations");
}

export function useRecommendationsApi() {
  return {
    fetchRecommendations,
  };
}
