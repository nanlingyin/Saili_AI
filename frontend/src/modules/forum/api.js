import { apiDelete, apiGet, apiPost } from "../../core/api/client";

export function fetchForumPosts(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      search.append(key, value);
    }
  });
  const query = search.toString();
  return apiGet(query ? `/forum/posts?${query}` : "/forum/posts");
}

export function fetchForumPost(postId) {
  return apiGet(`/forum/posts/${postId}`);
}

export function createForumPost(payload) {
  return apiPost("/forum/posts", payload);
}

export function createForumReply(postId, payload) {
  return apiPost(`/forum/posts/${postId}/replies`, payload);
}

export function togglePinPost(postId) {
  return apiPost(`/forum/posts/${postId}/pin`);
}

export function deleteForumPost(postId) {
  return apiDelete(`/forum/posts/${postId}`);
}

export function deleteForumReply(replyId) {
  return apiDelete(`/forum/replies/${replyId}`);
}

export function useForumApi() {
  return {
    fetchForumPosts,
    fetchForumPost,
    createForumPost,
    createForumReply,
    togglePinPost,
    deleteForumPost,
    deleteForumReply,
  };
}
