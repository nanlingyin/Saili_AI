<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">竞赛库</p>
      <h1 class="page-title">竞赛列表</h1>
      <p class="page-desc">按关键词与标签筛选已发布的竞赛信息。</p>
    </div>

    <div class="card">
      <div class="filters">
        <label class="field">
          <span class="field-label">关键词</span>
          <input v-model="query" class="input" placeholder="搜索竞赛名称" />
        </label>
        <label class="field">
          <span class="field-label">标签</span>
          <input v-model="tag" class="input" placeholder="如：编程" />
        </label>
        <button class="btn btn-primary btn-sm" @click="load">搜索</button>
      </div>
    </div>

    <ul class="grid grid-2">
      <li v-for="item in items" :key="item.id" class="card">
        <router-link :to="`/competitions/${item.id}`" class="card-title">
          {{ item.title }}
        </router-link>
        <p class="card-meta">{{ item.organizer || "未提供主办方" }}</p>
        <p class="card-meta">报名截止：{{ formatDate(item.signup_end) }}</p>
        <div class="tags" v-if="item.tags?.length">
          <span v-for="t in item.tags" :key="t" class="tag">{{ t }}</span>
        </div>
      </li>
    </ul>

    <p v-if="!items.length" class="empty">暂无竞赛数据</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { fetchCompetitions } from "../api";

const items = ref([]);
const query = ref("");
const tag = ref("");

function formatDate(value) {
  if (!value) return "--";
  return new Date(value).toLocaleDateString("zh-CN");
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
