import SmartMatchPage from "./pages/SmartMatchPage.vue";

export default {
  name: "match",
  routes: [
    {
      path: "/match",
      name: "smart-match",
      component: SmartMatchPage,
    },
  ],
  menus: [
    {
      path: "/match",
      label: "智能匹配",
    },
  ],
};
