import { apiDelete, apiGet, apiPost } from "../../core/api/client";

export function fetchFavorites() {
  return apiGet("/favorites");
}

export function addFavorite(id) {
  return apiPost(`/favorites/${id}`);
}

export function removeFavorite(id) {
  return apiDelete(`/favorites/${id}`);
}