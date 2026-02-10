import CompetitionDetailPage from "./pages/CompetitionDetailPage.vue";
import CompetitionListPage from "./pages/CompetitionListPage.vue";

export default {
  name: "competitions",
  routes: [
    {
      path: "/competitions",
      name: "competitions",
      component: CompetitionListPage,
    },
    {
      path: "/competitions/:id",
      name: "competition-detail",
      component: CompetitionDetailPage,
    },
  ],
  menus: [
    {
      path: "/competitions",
      label: "竞赛列表",
    },
  ],
};