import FavoritesPage from "./pages/FavoritesPage.vue";
import SubscriptionsPage from "./pages/SubscriptionsPage.vue";

export default {
  name: "favorites",
  routes: [
    {
      path: "/favorites",
      name: "favorites",
      component: FavoritesPage,
    },
    {
      path: "/subscriptions",
      name: "subscriptions",
      component: SubscriptionsPage,
    },
  ],
  menus: [
    {
      path: "/favorites",
      label: "收藏",
      requiresAuth: true,
    },
    {
      path: "/subscriptions",
      label: "订阅",
      requiresAuth: true,
    },
  ],
};
