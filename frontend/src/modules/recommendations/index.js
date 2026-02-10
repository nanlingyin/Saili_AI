import RecommendationsPage from "./pages/RecommendationsPage.vue";

export default {
  name: "recommendations",
  routes: [
    {
      path: "/recommendations",
      name: "recommendations",
      component: RecommendationsPage,
    },
  ],
  menus: [
    {
      path: "/recommendations",
      label: "推荐",
    },
  ],
};