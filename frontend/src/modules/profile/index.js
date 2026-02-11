import ProfilePage from "./pages/ProfilePage.vue";

export default {
  name: "profile",
  routes: [
    {
      path: "/profile",
      name: "profile",
      component: ProfilePage,
    },
  ],
  menus: [
    {
      path: "/profile",
      label: "我的",
      requiresAuth: true,
    },
  ],
};
