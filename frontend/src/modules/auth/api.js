import { apiPost } from "../../core/api/client";

export function login(payload) {
  return apiPost("/auth/login", payload);
}

export function register(payload) {
  return apiPost("/auth/register", payload);
}

export function useAuthApi() {
  return {
    login,
    register,
  };
}
