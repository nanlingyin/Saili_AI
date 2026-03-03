import AdminCompetitionsPage from "./pages/AdminCompetitionsPage.vue";
import AdminApiConfigPage from "./pages/AdminApiConfigPage.vue";
import AdminManagersPage from "./pages/AdminManagersPage.vue";

export default {
  name: "admin",
  routes: [
    {
      path: "/admin",
      name: "admin",
      component: AdminCompetitionsPage,
    },
    {
      path: "/admin/managers",
      name: "admin-managers",
      component: AdminManagersPage,
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
      requiresSchoolManager: true,
    },
    {
      path: "/admin/managers",
      label: "管理员配置",
      requiresAdmin: true,
    },
    {
      path: "/admin/api-config",
      label: "系统配置",
      requiresAdmin: true,
    },
  ],
};
