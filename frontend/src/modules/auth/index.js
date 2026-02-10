import LoginPage from "./pages/LoginPage.vue";

export default {
  name: "auth",
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginPage,
    },
  ],
  menus: [
    {
      path: "/login",
      label: "登录",
    },
  ],
};