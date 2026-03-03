import ReminderSettingsPage from "./pages/ReminderSettingsPage.vue";

export default {
  name: "reminders",
  routes: [
    {
      path: "/reminders/settings",
      name: "reminder-settings",
      component: ReminderSettingsPage,
    },
  ],
  menus: [
    {
      path: "/reminders/settings",
      label: "提醒",
      requiresAuth: true,
    },
  ],
};
