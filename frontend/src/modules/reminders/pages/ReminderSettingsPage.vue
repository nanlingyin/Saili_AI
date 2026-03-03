<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">提醒</p>
      <h1 class="page-title">提醒设置</h1>
      <p class="page-desc">设置在报名截止前多少天收到提醒（可多条）。</p>
    </div>

    <div v-if="!loggedIn" class="card" style="max-width: 480px">
      <p style="margin-bottom: 16px; color: var(--secondary)">登录后管理提醒设置。</p>
      <router-link to="/login" class="btn btn-primary">前往登录</router-link>
    </div>

    <template v-else>
      <div class="card" style="max-width: 640px; margin-bottom: 16px">
        <h2 class="section-title">快捷添加</h2>
        <div class="btn-group" style="margin-bottom: 16px">
          <button class="btn btn-secondary btn-sm" @click="quickSet(1)">截止前 1 天</button>
          <button class="btn btn-secondary btn-sm" @click="quickSet(3)">截止前 3 天</button>
          <button class="btn btn-secondary btn-sm" @click="quickSet(7)">截止前 7 天</button>
        </div>

        <form @submit.prevent="handleSave" class="form form-wide">
          <label class="field">
            <span class="field-label">提前天数</span>
            <input v-model.number="form.days_before" class="input" type="number" min="0" />
          </label>
          <label class="field" style="display:flex; align-items:center; gap:8px;">
            <input v-model="form.enabled" type="checkbox" />
            <span class="field-label" style="margin:0">启用此提醒</span>
          </label>
          <button class="btn btn-primary" type="submit">保存设置</button>
        </form>
      </div>

      <div v-if="message" class="msg" :class="msgClass" style="margin-bottom: 16px">{{ message }}</div>

      <div class="card">
        <h2 class="section-title">当前设置</h2>
        <ul class="grid" v-if="items.length">
          <li v-for="item in items" :key="item.days_before" class="card card-row">
            <div>
              <div class="card-title">截止前 {{ item.days_before }} 天</div>
              <p class="card-meta">状态：{{ item.enabled ? "已启用" : "已停用" }}</p>
            </div>
            <div class="btn-group">
              <button class="btn btn-secondary btn-sm" @click="toggleItem(item)">
                {{ item.enabled ? "停用" : "启用" }}
              </button>
            </div>
          </li>
        </ul>
        <p v-else class="empty">暂无提醒设置（注册默认会有 3 天提醒）</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRemindersApi } from "../api";
import { useAuth } from "../../../core/auth-store";

const { fetchReminderSettings, upsertReminderSetting } = useRemindersApi();
const { loggedIn } = useAuth();

const items = ref([]);
const message = ref("");
const msgClass = ref("msg-success");

const form = reactive({
  days_before: 3,
  enabled: true,
});

async function load() {
  if (!loggedIn.value) return;
  const data = await fetchReminderSettings();
  items.value = [...data].sort((a, b) => a.days_before - b.days_before);
}

async function quickSet(daysBefore) {
  message.value = "";
  try {
    await upsertReminderSetting({ days_before: daysBefore, enabled: true });
    message.value = `已添加：截止前 ${daysBefore} 天提醒`;
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "保存失败";
    msgClass.value = "msg-error";
  }
}

async function handleSave() {
  message.value = "";
  if (form.days_before < 0) {
    message.value = "提前天数不能小于 0";
    msgClass.value = "msg-error";
    return;
  }

  try {
    await upsertReminderSetting({
      days_before: form.days_before,
      enabled: form.enabled,
    });
    message.value = "提醒设置已保存";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "保存失败";
    msgClass.value = "msg-error";
  }
}

async function toggleItem(item) {
  message.value = "";
  try {
    await upsertReminderSetting({
      days_before: item.days_before,
      enabled: !item.enabled,
    });
    message.value = "状态已更新";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "更新失败";
    msgClass.value = "msg-error";
  }
}

onMounted(load);
</script>
