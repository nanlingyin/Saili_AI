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

export function fetchSubscriptions() {
  return apiGet("/subscriptions");
}

export function addSubscription(payload) {
  return apiPost("/subscriptions", payload);
}

export function removeSubscription(subscriptionType, target) {
  const query = new URLSearchParams({
    subscription_type: subscriptionType,
    target,
  });
  return apiDelete(`/subscriptions?${query.toString()}`);
}

export function useFavoritesApi() {
  return {
    fetchFavorites,
    addFavorite,
    removeFavorite,
    fetchSubscriptions,
    addSubscription,
    removeSubscription,
  };
}
