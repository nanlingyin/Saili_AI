import CompetitionDetailPage from "./pages/CompetitionDetailPage.vue";
import CompetitionListPage from "./pages/CompetitionListPage.vue";
import NationalCompetitionsPage from "./pages/NationalCompetitionsPage.vue";

export default {
  name: "competitions",
  routes: [
    {
      path: "/competitions",
      name: "competitions",
      component: CompetitionListPage,
    },
    {
      path: "/competitions/national",
      name: "national-competitions",
      component: NationalCompetitionsPage,
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
    {
      path: "/competitions/national",
      label: "国家认可",
    },
  ],
};
