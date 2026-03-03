import { apiGet, apiPost } from "../../core/api/client";

export function fetchSkillTags() {
  return apiGet("/teams/skill-tags");
}

export function createTeam(payload) {
  return apiPost("/teams", payload);
}

export function addTeamMember(teamId, payload) {
  return apiPost(`/teams/${teamId}/members`, payload);
}

export function kickTeamMember(teamId, userId) {
  return apiPost(`/teams/${teamId}/members/${userId}/kick`);
}

export function fetchMemberCredit(teamId, userId) {
  return apiGet(`/teams/${teamId}/members/${userId}/credit`);
}

export function createTeamTask(teamId, payload) {
  return apiPost(`/teams/${teamId}/tasks`, payload);
}

export function checkinTask(taskId, payload) {
  return apiPost(`/teams/tasks/${taskId}/checkin`, payload);
}

export function auditOverdueTasks(teamId) {
  return apiPost(`/teams/${teamId}/tasks/audit-overdue`);
}

export function useTeamsApi() {
  return {
    fetchSkillTags,
    createTeam,
    addTeamMember,
    kickTeamMember,
    fetchMemberCredit,
    createTeamTask,
    checkinTask,
    auditOverdueTasks,
  };
}
