<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">竞赛简历</p>
      <h1 class="page-title">获奖记录与导出</h1>
      <p class="page-desc">维护个人获奖记录，一键导出 PDF 简历。</p>
    </div>

    <div v-if="!loggedIn" class="card" style="max-width: 480px">
      <p style="margin-bottom: 16px; color: var(--secondary)">登录后管理竞赛简历。</p>
      <router-link to="/login" class="btn btn-primary">前往登录</router-link>
    </div>

    <template v-else>
      <div class="card" style="max-width: 640px">
        <h2 class="section-title">新增获奖记录</h2>
        <form @submit.prevent="handleCreate" class="form form-wide">
          <label class="field">
            <span class="field-label">竞赛名称</span>
            <input v-model="form.competition_name" class="input" placeholder="示例：挑战杯" />
          </label>
          <label class="field">
            <span class="field-label">奖项名称</span>
            <input v-model="form.award_name" class="input" placeholder="示例：省一等奖" />
          </label>
          <label class="field">
            <span class="field-label">年份</span>
            <input v-model.number="form.year" class="input" type="number" min="1900" max="2100" />
          </label>
          <div class="btn-group">
            <button class="btn btn-primary" type="submit">保存记录</button>
            <button class="btn btn-secondary" type="button" @click="handleDownload">导出 PDF</button>
          </div>
        </form>
      </div>

      <div v-if="message" class="msg" :class="msgClass">{{ message }}</div>

      <div class="card">
        <h2 class="section-title">记录列表</h2>
        <ul class="grid" v-if="items.length">
          <li v-for="item in items" :key="item.id" class="card card-row">
            <div>
              <div class="card-title">{{ item.competition_name }}</div>
              <p class="card-meta">奖项：{{ item.award_name }}</p>
              <p class="card-meta">年份：{{ item.year }}</p>
            </div>
          </li>
        </ul>
        <p v-else class="empty">暂无获奖记录</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";

import { useAuth } from "../../../core/auth-store";
import { useResumeApi } from "../api";

const { loggedIn } = useAuth();
const { fetchResumeRecords, createResumeRecord, downloadResumePdf } = useResumeApi();

const items = ref([]);
const message = ref("");
const msgClass = ref("msg-success");

const form = reactive({
  competition_name: "",
  award_name: "",
  year: new Date().getFullYear(),
});

async function load() {
  if (!loggedIn.value) return;
  items.value = await fetchResumeRecords();
}

async function handleCreate() {
  message.value = "";
  const payload = {
    competition_name: form.competition_name.trim(),
    award_name: form.award_name.trim(),
    year: Number(form.year),
  };

  if (!payload.competition_name || !payload.award_name || !payload.year) {
    message.value = "请完整填写竞赛名称、奖项与年份";
    msgClass.value = "msg-error";
    return;
  }

  try {
    await createResumeRecord(payload);
    form.competition_name = "";
    form.award_name = "";
    form.year = new Date().getFullYear();
    message.value = "记录已保存";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "保存失败";
    msgClass.value = "msg-error";
  }
}

async function handleDownload() {
  message.value = "";
  try {
    const blob = await downloadResumePdf();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "competition_resume.pdf";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    message.value = "PDF 已开始下载";
    msgClass.value = "msg-success";
  } catch (err) {
    message.value = err instanceof Error ? err.message : "下载失败";
    msgClass.value = "msg-error";
  }
}

onMounted(load);
</script>
