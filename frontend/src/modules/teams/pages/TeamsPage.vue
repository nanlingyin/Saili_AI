<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">团队协作</p>
      <h1 class="page-title">组队与任务管理</h1>
      <p class="page-desc">覆盖创建团队、成员管理、任务打卡、信用查看与逾期审计。</p>
    </div>

    <div v-if="!loggedIn" class="card" style="max-width: 480px">
      <p style="margin-bottom: 16px; color: var(--secondary)">登录后使用组队协作能力。</p>
      <router-link to="/login" class="btn btn-primary">前往登录</router-link>
    </div>

    <template v-else>
      <div class="card">
        <h2 class="section-title">技能标签</h2>
        <div class="tags" v-if="skillTags.length">
          <span v-for="tag in skillTags" :key="tag" class="tag">{{ tag }}</span>
        </div>
        <p class="card-meta" v-else>暂无技能标签</p>
      </div>

      <div v-if="message" class="msg" :class="msgClass">{{ message }}</div>

      <div class="card">
        <h2 class="section-title">创建团队</h2>
        <form class="form form-wide" @submit.prevent="handleCreateTeam">
          <label class="field">
            <span class="field-label">团队名</span>
            <input v-model="createTeamForm.name" class="input" placeholder="示例：数模冲刺队" />
          </label>
          <label class="field">
            <span class="field-label">学校（可选）</span>
            <input v-model="createTeamForm.school" class="input" placeholder="示例：清华大学" />
          </label>
          <label class="field">
            <span class="field-label">需求技能</span>
            <div class="checkbox-group">
              <label v-for="tag in skillTags" :key="`create-${tag}`" class="checkbox-item">
                <input type="checkbox" :value="tag" v-model="createTeamForm.required_skills" />
                <span>{{ tag }}</span>
              </label>
            </div>
          </label>
          <button class="btn btn-primary" type="submit">创建团队</button>
        </form>
        <p v-if="latestTeam" class="card-meta" style="margin-top: 12px">
          最近创建团队：ID {{ latestTeam.id }}，名称 {{ latestTeam.name }}
        </p>
      </div>

      <div class="card">
        <h2 class="section-title">成员管理</h2>
        <form class="form form-wide" @submit.prevent="handleAddMember">
          <label class="field">
            <span class="field-label">团队 ID</span>
            <input v-model.number="memberForm.team_id" class="input" type="number" min="1" />
          </label>
          <label class="field">
            <span class="field-label">成员用户 ID</span>
            <input v-model.number="memberForm.user_id" class="input" type="number" min="1" />
          </label>
          <label class="field">
            <span class="field-label">成员技能</span>
            <div class="checkbox-group">
              <label v-for="tag in skillTags" :key="`member-${tag}`" class="checkbox-item">
                <input type="checkbox" :value="tag" v-model="memberForm.skills" />
                <span>{{ tag }}</span>
              </label>
            </div>
          </label>
          <div class="btn-group">
            <button class="btn btn-primary" type="submit">添加成员</button>
            <button class="btn btn-secondary" type="button" @click="handleKickMember">踢出成员</button>
            <button class="btn btn-secondary" type="button" @click="handleFetchCredit">查看信用</button>
          </div>
        </form>

        <div v-if="credit" class="detail-grid" style="margin-top: 16px">
          <div class="detail-item">
            <div class="detail-label">用户ID</div>
            <div class="detail-value">{{ credit.user_id }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">被踢次数</div>
            <div class="detail-value">{{ credit.kicked_count }}</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">完成率</div>
            <div class="detail-value">{{ (credit.completion_rate * 100).toFixed(1) }}%</div>
          </div>
          <div class="detail-item">
            <div class="detail-label">缺勤次数</div>
            <div class="detail-value">{{ credit.missed_checkins }}</div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2 class="section-title">任务管理</h2>
        <form class="form form-wide" @submit.prevent="handleCreateTask">
          <label class="field">
            <span class="field-label">团队 ID</span>
            <input v-model.number="taskCreateForm.team_id" class="input" type="number" min="1" />
          </label>
          <label class="field">
            <span class="field-label">执行人用户 ID</span>
            <input v-model.number="taskCreateForm.assignee_user_id" class="input" type="number" min="1" />
          </label>
          <label class="field">
            <span class="field-label">任务标题</span>
            <input v-model="taskCreateForm.title" class="input" placeholder="示例：完成报名材料初稿" />
          </label>
          <label class="field">
            <span class="field-label">任务说明（可选）</span>
            <textarea v-model="taskCreateForm.description" class="input" rows="3"></textarea>
          </label>
          <label class="field">
            <span class="field-label">截止时间（可选）</span>
            <input v-model="taskCreateForm.due_at" class="input" type="datetime-local" />
          </label>
          <button class="btn btn-primary" type="submit">创建任务</button>
        </form>

        <p v-if="createdTaskId" class="card-meta" style="margin-top: 12px">最近创建任务 ID：{{ createdTaskId }}</p>

        <hr class="divider" />

        <form class="form form-wide" @submit.prevent="handleCheckinTask">
          <label class="field">
            <span class="field-label">任务 ID</span>
            <input v-model.number="taskCheckinForm.task_id" class="input" type="number" min="1" />
          </label>
          <label class="field">
            <span class="field-label">打卡说明（可选）</span>
            <input v-model="taskCheckinForm.note" class="input" placeholder="示例：已提交初稿" />
          </label>
          <button class="btn btn-secondary" type="submit">任务打卡完成</button>
        </form>

        <hr class="divider" />

        <form class="form form-wide" @submit.prevent="handleAuditOverdue">
          <label class="field">
            <span class="field-label">审计团队 ID</span>
            <input v-model.number="auditForm.team_id" class="input" type="number" min="1" />
          </label>
          <button class="btn btn-secondary" type="submit">审计逾期任务</button>
        </form>
      </div>
    </template>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";

import { useAuth } from "../../../core/auth-store";
import { useTeamsApi } from "../api";

const {
  fetchSkillTags,
  createTeam,
  addTeamMember,
  kickTeamMember,
  fetchMemberCredit,
  createTeamTask,
  checkinTask,
  auditOverdueTasks,
} = useTeamsApi();
const { loggedIn } = useAuth();

const skillTags = ref([]);
const latestTeam = ref(null);
const credit = ref(null);
const createdTaskId = ref(0);
const message = ref("");
const msgClass = ref("msg-success");

const createTeamForm = reactive({
  name: "",
  school: "",
  required_skills: [],
});

const memberForm = reactive({
  team_id: 0,
  user_id: 0,
  skills: [],
});

const taskCreateForm = reactive({
  team_id: 0,
  assignee_user_id: 0,
  title: "",
  description: "",
  due_at: "",
});

const taskCheckinForm = reactive({
  task_id: 0,
  note: "",
});

const auditForm = reactive({
  team_id: 0,
});

function ok(text) {
  message.value = text;
  msgClass.value = "msg-success";
}

function fail(err, fallback) {
  message.value = err instanceof Error ? err.message : fallback;
  msgClass.value = "msg-error";
}

function ensurePositiveInt(value) {
  const num = Number(value);
  return Number.isInteger(num) && num > 0 ? num : 0;
}

function initTeamId(teamId) {
  if (!memberForm.team_id) memberForm.team_id = teamId;
  if (!taskCreateForm.team_id) taskCreateForm.team_id = teamId;
  if (!auditForm.team_id) auditForm.team_id = teamId;
}

async function loadSkillTags() {
  if (!loggedIn.value) return;
  try {
    skillTags.value = await fetchSkillTags();
  } catch (err) {
    fail(err, "加载技能标签失败");
  }
}

async function handleCreateTeam() {
  message.value = "";
  const payload = {
    name: createTeamForm.name.trim(),
    school: createTeamForm.school.trim(),
    required_skills: createTeamForm.required_skills,
  };
  if (!payload.name) {
    message.value = "请输入团队名称";
    msgClass.value = "msg-error";
    return;
  }

  try {
    const team = await createTeam(payload);
    latestTeam.value = team;
    initTeamId(team.id);
    createTeamForm.name = "";
    createTeamForm.school = "";
    createTeamForm.required_skills = [];
    ok(`团队创建成功，ID ${team.id}`);
  } catch (err) {
    fail(err, "创建团队失败");
  }
}

async function handleAddMember() {
  message.value = "";
  const teamId = ensurePositiveInt(memberForm.team_id);
  const userId = ensurePositiveInt(memberForm.user_id);
  if (!teamId || !userId) {
    message.value = "请填写有效的团队 ID 和用户 ID";
    msgClass.value = "msg-error";
    return;
  }

  try {
    await addTeamMember(teamId, {
      user_id: userId,
      skills: memberForm.skills,
    });
    ok("成员添加成功");
  } catch (err) {
    fail(err, "添加成员失败");
  }
}

async function handleKickMember() {
  message.value = "";
  const teamId = ensurePositiveInt(memberForm.team_id);
  const userId = ensurePositiveInt(memberForm.user_id);
  if (!teamId || !userId) {
    message.value = "请填写有效的团队 ID 和用户 ID";
    msgClass.value = "msg-error";
    return;
  }

  try {
    await kickTeamMember(teamId, userId);
    ok("成员已踢出");
  } catch (err) {
    fail(err, "踢人失败");
  }
}

async function handleFetchCredit() {
  message.value = "";
  const teamId = ensurePositiveInt(memberForm.team_id);
  const userId = ensurePositiveInt(memberForm.user_id);
  if (!teamId || !userId) {
    message.value = "请填写有效的团队 ID 和用户 ID";
    msgClass.value = "msg-error";
    return;
  }

  try {
    credit.value = await fetchMemberCredit(teamId, userId);
    ok("已获取成员信用");
  } catch (err) {
    fail(err, "获取信用失败");
  }
}

async function handleCreateTask() {
  message.value = "";
  const teamId = ensurePositiveInt(taskCreateForm.team_id);
  const assigneeUserId = ensurePositiveInt(taskCreateForm.assignee_user_id);
  if (!teamId || !assigneeUserId || !taskCreateForm.title.trim()) {
    message.value = "请填写团队 ID、执行人 ID 和任务标题";
    msgClass.value = "msg-error";
    return;
  }

  const payload = {
    assignee_user_id: assigneeUserId,
    title: taskCreateForm.title.trim(),
    description: taskCreateForm.description.trim() || undefined,
    due_at: taskCreateForm.due_at ? new Date(taskCreateForm.due_at).toISOString() : undefined,
  };

  try {
    const data = await createTeamTask(teamId, payload);
    createdTaskId.value = data.id;
    taskCreateForm.title = "";
    taskCreateForm.description = "";
    taskCreateForm.due_at = "";
    if (!taskCheckinForm.task_id) {
      taskCheckinForm.task_id = data.id;
    }
    ok(`任务创建成功，ID ${data.id}`);
  } catch (err) {
    fail(err, "创建任务失败");
  }
}

async function handleCheckinTask() {
  message.value = "";
  const taskId = ensurePositiveInt(taskCheckinForm.task_id);
  if (!taskId) {
    message.value = "请填写有效任务 ID";
    msgClass.value = "msg-error";
    return;
  }

  try {
    await checkinTask(taskId, {
      note: taskCheckinForm.note.trim() || undefined,
    });
    ok("任务打卡完成");
  } catch (err) {
    fail(err, "任务打卡失败");
  }
}

async function handleAuditOverdue() {
  message.value = "";
  const teamId = ensurePositiveInt(auditForm.team_id);
  if (!teamId) {
    message.value = "请填写有效团队 ID";
    msgClass.value = "msg-error";
    return;
  }

  try {
    const data = await auditOverdueTasks(teamId);
    ok(`审计完成：标记逾期 ${data.overdue_flagged} 条，更新用户 ${data.users_updated} 人`);
  } catch (err) {
    fail(err, "逾期审计失败");
  }
}

onMounted(loadSkillTags);
</script>
