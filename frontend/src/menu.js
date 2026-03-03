import { getMenus } from "./core/extensions";
import { authStore } from "./core/auth-store";

export function getMenuItems() {
  const all = [
    { path: "/", label: "首页" },
    ...getMenus(),
  ];

  return all.filter((item) => {
    if (item.guestOnly && authStore.loggedIn) return false;
    if (item.requiresAuth && !authStore.loggedIn) return false;
    if (item.requiresAdmin && !authStore.isAdmin) return false;
    if (item.requiresSchoolManager && !authStore.isSchoolManager) return false;
    return true;
  });
}