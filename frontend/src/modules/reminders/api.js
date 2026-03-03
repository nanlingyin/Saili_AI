import { apiGet, apiPost } from "../../core/api/client";

export function fetchReminderSettings() {
  return apiGet("/reminders/settings");
}

export function upsertReminderSetting(payload) {
  return apiPost("/reminders/settings", payload);
}

export function useRemindersApi() {
  return {
    fetchReminderSettings,
    upsertReminderSetting,
  };
}
