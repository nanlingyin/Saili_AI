import AdminCompetitionsPage from "./pages/AdminCompetitionsPage.vue";
import AdminApiConfigPage from "./pages/AdminApiConfigPage.vue";

export default {
  name: "admin",
  routes: [
    {
      path: "/admin",
      name: "admin",
      component: AdminCompetitionsPage,
    },
    {
      path: "/admin/api-config",
      name: "admin-api-config",
      component: AdminApiConfigPage,
    },
  ],
  menus: [
    {
      path: "/admin",
      label: "管理后台",
      requiresAdmin: true,
    },
  ],
};
