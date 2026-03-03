import { apiGet, apiPost } from "../../core/api/client";

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

export function enrollCompetition(id) {
  return apiPost(`/competitions/${id}/enroll`);
}

export function submitCompetition(id) {
  return apiPost(`/competitions/${id}/submit`);
}

export function useCompetitionsApi() {
  return {
    fetchCompetitions,
    fetchCompetition,
    enrollCompetition,
    submitCompetition,
  };
}
