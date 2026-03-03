import ResumePage from "./pages/ResumePage.vue";

export default {
  name: "resume",
  routes: [
    {
      path: "/resume",
      name: "resume",
      component: ResumePage,
    },
  ],
  menus: [
    {
      path: "/resume",
      label: "竞赛简历",
      requiresAuth: true,
    },
  ],
};
