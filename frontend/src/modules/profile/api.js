import { apiGet, apiPut } from "../../core/api/client";

export function getProfile() {
  return apiGet("/profile");
}

export function updateProfile(payload) {
  return apiPut("/profile", payload);
}

export function useProfileApi() {
  return {
    getProfile,
    updateProfile,
  };
}
