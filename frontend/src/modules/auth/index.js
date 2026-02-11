import LoginPage from "./pages/LoginPage.vue";
import RegisterPage from "./pages/RegisterPage.vue";

export default {
  name: "auth",
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginPage,
    },
    {
      path: "/register",
      name: "register",
      component: RegisterPage,
    },
  ],
  menus: [
    {
      path: "/login",
      label: "登录",
      guestOnly: true,
    },
    {
      path: "/register",
      label: "注册",
      guestOnly: true,
    },
  ],
};