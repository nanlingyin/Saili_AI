import { apiGet } from "../../core/api/client";

export function fetchCompetitions(params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      searchParams.append(key, value);
    }
  });
  const query = searchParams.toString();
  const path = query ? `/competitions?${query}` : "/competitions";
  return apiGet(path);
}

export function fetchCompetition(id) {
  return apiGet(`/competitions/${id}`);
}
