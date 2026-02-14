import { apiPost } from "../../core/api/client";

export function matchByMajor(major, topK = 8) {
  return apiPost("/match", { major, top_k: topK });
}
