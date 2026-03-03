import { apiDownload, apiGet, apiPost, apiPut } from "../../core/api/client";

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

export function unpublishCompetition(id) {
  return apiPost(`/admin/competitions/${id}/unpublish`);
}

export function ingestSource() {
  return apiPost("/admin/ingest/source");
}

export function updateCompetition(id, payload) {
  return apiPut(`/admin/competitions/${id}`, payload);
}

export function fetchCompetitionRegistrations(id) {
  return apiGet(`/admin/competitions/${id}/registrations`);
}

export function downloadCompetitionRegistrationsCsv(id) {
  return apiDownload(`/admin/competitions/${id}/registrations/export.csv`);
}

export function fetchIngestionSources() {
  return apiGet("/admin/ingest/sources");
}

export function fetchApiProviders() {
  return apiGet("/admin/config/api-providers");
}

export function updateApiProviders(payload) {
  return apiPut("/admin/config/api-providers", payload);
}

export function fetchSchoolManagers(school) {
  const query = school ? `?school=${encodeURIComponent(school)}` : "";
  return apiGet(`/admin/schools/admins${query}`);
}

export function createSchoolManager(payload) {
  return apiPost("/admin/schools/admins", payload);
}

export function updateSchoolManagerRole(payload) {
  return apiPut("/admin/schools/admins/role", payload);
}

export function updateRecommendationRules(payload) {
  return apiPut("/admin/recommendation-rules", payload);
}

export function sendDueReminders() {
  return apiPost("/admin/reminders/send");
}

export function useAdminApi() {
  return {
    fetchCompetitions,
    createCompetition,
    publishCompetition,
    unpublishCompetition,
    ingestSource,
    updateCompetition,
    fetchCompetitionRegistrations,
    downloadCompetitionRegistrationsCsv,
    fetchIngestionSources,
    fetchApiProviders,
    updateApiProviders,
    fetchSchoolManagers,
    createSchoolManager,
    updateSchoolManagerRole,
    updateRecommendationRules,
    sendDueReminders,
  };
}
