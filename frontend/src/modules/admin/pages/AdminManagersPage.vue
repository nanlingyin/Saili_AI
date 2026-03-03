<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">管理</p>
      <h1 class="page-title">学校管理员配置</h1>
      <p class="page-desc">平台管理员可创建并调整学校管理员/学生管理员角色与归属学校。</p>
    </div>

    <div class="card" style="max-width: 760px" v-if="isAdmin">
      <h2 class="section-title">新增管理员</h2>
      <p class="card-meta" style="margin-bottom: 10px">示例：学校“清华大学”，可配置 1 个学校管理员 + 多个学生管理员。</p>
      <form @submit.prevent="handleCreate" class="form form-wide">
        <label class="field">
          <span class="field-label">用户名</span>
          <input v-model="form.username" class="input" placeholder="示例：thu_admin_01" />
        </label>
        <label class="field">
          <span class="field-label">邮箱</span>
          <input v-model="form.email" class="input" placeholder="示例：admin01@thu.edu.cn" />
        </label>
        <label class="field">
          <span class="field-label">密码</span>
          <input v-model="form.password" class="input" type="password" placeholder="请输入初始密码" />
        </label>
        <label class="field">
          <span class="field-label">角色</span>
          <select v-model="form.role" class="input">
            <option value="school_admin">学校管理员</option>
            <option value="student_admin">学生管理员</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label">学校</span>
          <input v-model="form.school" class="input" placeholder="示例：清华大学" />
        </label>
        <button class="btn btn-primary" type="submit">创建管理员</button>
      </form>
    </div>

    <div v-else class="card">
      <p class="empty">仅平台管理员可访问此页面。</p>
    </div>

    <div v-if="message" class="msg" :class="msgClass">{{ message }}</div>

    <div class="card" v-if="isAdmin">
      <h2 class="section-title">管理员列表</h2>
      <ul class="grid" v-if="items.length">
        <li v-for="item in items" :key="item.id" class="card">
          <div class="card-row">
            <div>
              <div class="card-title">{{ item.username }}</div>
              <p class="card-meta">{{ item.email }}</p>
            </div>
            <span class="tag">ID {{ item.id }}</span>
          </div>

          <div class="form form-wide" style="margin-top: 12px">
            <label class="field">
              <span class="field-label">角色</span>
              <select v-model="editState[item.id].role" class="input">
                <option value="school_admin">学校管理员</option>
                <option value="student_admin">学生管理员</option>
                <option value="student">普通学生</option>
              </select>
            </label>
            <label class="field">
              <span class="field-label">学校</span>
              <input v-model="editState[item.id].school" class="input" />
            </label>
            <div class="btn-group">
              <button class="btn btn-secondary btn-sm" @click="handleUpdate(item.id)">更新角色/学校</button>
            </div>
          </div>
        </li>
      </ul>
      <p v-else class="empty">暂无学校管理员/学生管理员</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";

import { useAuth } from "../../../core/auth-store";
import { useAdminApi } from "../api";

const { isAdmin } = useAuth();
const { fetchSchoolManagers, createSchoolManager, updateSchoolManagerRole } = useAdminApi();

const items = ref([]);
const editState = reactive({});
const message = ref("");
const msgClass = ref("msg-success");

const form = reactive({
  username: "",
  email: "",
  password: "",
  role: "school_admin",
  school: "",
});

function ok(text) {
  message.value = text;
  msgClass.value = "msg-success";
}

function fail(err, fallback) {
  message.value = err instanceof Error ? err.message : fallback;
  msgClass.value = "msg-error";
}

function initEditState(list) {
  for (const item of list) {
    editState[item.id] = {
      role: item.role,
      school: item.school,
    };
  }
}

async function load() {
  if (!isAdmin.value) return;
  const list = await fetchSchoolManagers();
  items.value = list;
  initEditState(list);
}

async function handleCreate() {
  message.value = "";
  try {
    await createSchoolManager({
      username: form.username,
      email: form.email,
      password: form.password,
      role: form.role,
      school: form.school,
    });
    form.username = "";
    form.email = "";
    form.password = "";
    form.role = "school_admin";
    form.school = "";
    ok("管理员创建成功");
    await load();
  } catch (err) {
    fail(err, "创建失败");
  }
}

async function handleUpdate(userId) {
  message.value = "";
  const state = editState[userId];
  if (!state) return;

  try {
    await updateSchoolManagerRole({
      user_id: userId,
      role: state.role,
      school: state.school,
    });
    ok("角色配置已更新");
    await load();
  } catch (err) {
    fail(err, "更新失败");
  }
}

onMounted(async () => {
  try {
    await load();
  } catch (err) {
    fail(err, "加载管理员列表失败");
  }
});
</script>
