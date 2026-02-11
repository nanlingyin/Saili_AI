import { reactive, computed } from "vue";

const state = reactive({
  token: localStorage.getItem("auth_token") || "",
  user: JSON.parse(localStorage.getItem("auth_user") || "null"),
});

export const authStore = {
  get loggedIn() {
    return !!state.token;
  },
  get user() {
    return state.user;
  },
  get isAdmin() {
    return state.user?.is_admin === true;
  },
  get username() {
    return state.user?.username || "";
  },

  login(data) {
    state.token = data.access_token;
    state.user = data;
    localStorage.setItem("auth_token", data.access_token);
    localStorage.setItem("auth_user", JSON.stringify(data));
  },

  logout() {
    state.token = "";
    state.user = null;
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
  },
};

export function useAuth() {
  return {
    loggedIn: computed(() => authStore.loggedIn),
    user: computed(() => authStore.user),
    isAdmin: computed(() => authStore.isAdmin),
    username: computed(() => authStore.username),
    login: authStore.login,
    logout: authStore.logout,
  };
}
