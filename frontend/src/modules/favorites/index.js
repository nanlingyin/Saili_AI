import FavoritesPage from "./pages/FavoritesPage.vue";

export default {
  name: "favorites",
  routes: [
    {
      path: "/favorites",
      name: "favorites",
      component: FavoritesPage,
    },
  ],
  menus: [
    {
      path: "/favorites",
      label: "收藏",
    },
  ],
};