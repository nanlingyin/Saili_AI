import SamplePage from "./pages/SamplePage.vue";

export default {
  name: "sample",
  routes: [
    {
      path: "/sample",
      name: "sample",
      component: SamplePage,
    },
  ],
  menus: [
    {
      path: "/sample",
      label: "示例模块",
    },
  ],
};