import TeamsPage from "./pages/TeamsPage.vue";

export default {
  name: "teams",
  routes: [
    {
      path: "/teams",
      name: "teams",
      component: TeamsPage,
    },
  ],
  menus: [
    {
      path: "/teams",
      label: "组队协作",
      requiresAuth: true,
    },
  ],
};
