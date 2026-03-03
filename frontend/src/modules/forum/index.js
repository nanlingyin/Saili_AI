import ForumPage from "./pages/ForumPage.vue";

export default {
  name: "forum",
  routes: [
    {
      path: "/forum",
      name: "forum",
      component: ForumPage,
    },
  ],
  menus: [
    {
      path: "/forum",
      label: "校园论坛",
      requiresAuth: true,
    },
  ],
};
