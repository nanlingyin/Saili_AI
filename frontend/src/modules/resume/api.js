import { apiDownload, apiGet, apiPost } from "../../core/api/client";

export function fetchResumeRecords() {
  return apiGet("/resume/records");
}

export function createResumeRecord(payload) {
  return apiPost("/resume/records", payload);
}

export function downloadResumePdf() {
  return apiDownload("/resume/pdf");
}

export function useResumeApi() {
  return {
    fetchResumeRecords,
    createResumeRecord,
    downloadResumePdf,
  };
}
