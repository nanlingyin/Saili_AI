<template>
  <section class="page">
    <div class="panel">
      <p class="eyebrow">管理</p>
      <h1 class="page-title">管理后台</h1>
      <p class="page-subtitle">审核、编辑与发布竞赛数据。</p>
      <div class="hero-actions">
        <button class="btn btn-primary" @click="handleIngest">导入稳定数据源</button>
        <router-link class="btn btn-ghost" to="/admin/api-config">API 配置</router-link>
      </div>
    </div>

    <div class="panel">
      <h2 class="section-title">待审核竞赛</h2>
      <ul class="list-grid">
        <li v-for="item in pending" :key="item.id" class="card card-row">
          <div>
            <div class="card-title">{{ item.title }}</div>
            <p class="card-meta">来源：{{ item.source }}</p>
          </div>
          <div class="hero-actions">
            <button class="btn btn-ghost" @click="publish(item.id)">发布</button>
          </div>
        </li>
      </ul>
    </div>

    <div class="panel">
      <h2 class="section-title">手动录入</h2>
      <form @submit.prevent="handleCreate" class="form-grid">
        <label class="field">
          <span>竞赛标题</span>
          <input v-model="form.title" class="input" required />
        </label>
        <label class="field">
          <span>主办方</span>
          <input v-model="form.organizer" class="input" />
        </label>
        <label class="field">
          <span>标签（逗号分隔）</span>
          <input v-model="form.tags" class="input" />
        </label>
        <button class="btn btn-primary" type="submit">提交</button>
      </form>
      <p v-if="message" class="message">{{ message }}</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";

import { createCompetition, fetchCompetitions, ingestSource, publishCompetition } from "../api";

const pending = ref([]);
const message = ref("");
const form = reactive({
  title: "",
  organizer: "",
  tags: "",
});

async function load() {
  pending.value = await fetchCompetitions("pending");
}

async function publish(id) {
  await publishCompetition(id);
  await load();
}

async function handleIngest() {
  message.value = "";
  try {
    await ingestSource();
    message.value = "导入完成";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "导入失败";
  }
}

async function handleCreate() {
  message.value = "";
  try {
    await createCompetition({
      title: form.title,
      organizer: form.organizer || undefined,
      tags: form.tags ? form.tags.split(",").map((item) => item.trim()) : [],
    });
    form.title = "";
    form.organizer = "";
    form.tags = "";
    message.value = "已提交，等待审核";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "提交失败";
  }
}

onMounted(load);
</script>
