<template>
  <section class="page">
    <div class="panel">
      <p class="eyebrow">竞赛库</p>
      <h1 class="page-title">竞赛列表</h1>
      <p class="page-subtitle">按关键词与标签筛选已发布竞赛。</p>

      <div class="filters">
        <label class="field">
          <span>关键词</span>
          <input v-model="query" class="input" placeholder="搜索关键词" />
        </label>
        <label class="field">
          <span>标签</span>
          <input v-model="tag" class="input" placeholder="标签" />
        </label>
        <button class="btn btn-primary" @click="load">搜索</button>
      </div>
    </div>

    <ul class="list-grid cols-2">
      <li v-for="item in items" :key="item.id" class="card">
        <router-link :to="`/competitions/${item.id}`" class="card-title">
          {{ item.title }}
        </router-link>
        <p class="card-meta">{{ item.organizer || "未提供主办方" }}</p>
        <p class="card-meta">报名截止：{{ formatDate(item.signup_end) }}</p>
        <div class="chips">
          <span v-for="tagItem in item.tags" :key="tagItem" class="chip">
            {{ tagItem }}
          </span>
        </div>
      </li>
    </ul>

    <p v-if="!items.length" class="empty">暂无竞赛</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";

import { fetchCompetitions } from "../api";

const items = ref([]);
const query = ref("");
const tag = ref("");

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

async function load() {
  const data = await fetchCompetitions({
    q: query.value || undefined,
    tag: tag.value || undefined,
  });
  items.value = data.items || [];
}

onMounted(load);
</script>
