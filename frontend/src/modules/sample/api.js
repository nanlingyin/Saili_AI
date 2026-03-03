import { apiGet } from "../../core/api/client";

export async function fetchHello() {
  return apiGet("/sample/hello");
}

export function useSampleApi() {
  return {
    fetchHello,
  };
}
