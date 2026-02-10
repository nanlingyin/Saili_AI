import { getMenus } from "./core/extensions";

export function getMenuItems() {
  return [
    { path: "/", label: "首页" },
    ...getMenus(),
  ];
}