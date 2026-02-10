import { createRouter, createWebHistory } from "vue-router";

import { getRoutes } from "./core/extensions";
import HomePage from "./pages/HomePage.vue";

export function createAppRouter() {
  const routes = [
    { path: "/", name: "home", component: HomePage },
    ...getRoutes(),
  ];

  return createRouter({
    history: createWebHistory(),
    routes,
  });
}