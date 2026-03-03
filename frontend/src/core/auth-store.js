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
  get role() {
    return state.user?.role || "student";
  },
  get school() {
    return state.user?.school || "";
  },
  get isSchoolManager() {
    return state.user?.is_admin === true || ["school_admin", "student_admin"].includes(state.user?.role);
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
    role: computed(() => authStore.role),
    school: computed(() => authStore.school),
    isSchoolManager: computed(() => authStore.isSchoolManager),
    username: computed(() => authStore.username),
    login: authStore.login,
    logout: authStore.logout,
  };
}
