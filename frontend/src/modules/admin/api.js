import { apiGet, apiPost, apiPut } from "../../core/api/client";

export function fetchCompetitions(status) {
  const query = status ? `?status=${status}` : "";
  return apiGet(`/admin/competitions${query}`);
}

export function createCompetition(payload) {
  return apiPost("/admin/competitions", payload);
}

export function publishCompetition(id) {
  return apiPost(`/admin/competitions/${id}/publish`);
}

export function ingestSource() {
  return apiPost("/admin/ingest/source");
}

export function updateCompetition(id, payload) {
  return apiPut(`/admin/competitions/${id}`, payload);
}

export function fetchApiProviders() {
  return apiGet("/admin/config/api-providers");
}

export function updateApiProviders(payload) {
  return apiPut("/admin/config/api-providers", payload);
}
