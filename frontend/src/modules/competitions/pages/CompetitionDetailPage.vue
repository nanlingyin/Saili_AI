<template>
  <section v-if="competition" class="page">
    <div class="panel">
      <p class="eyebrow">竞赛详情</p>
      <h1 class="page-title">{{ competition.title }}</h1>
      <p class="page-subtitle">{{ competition.description || "暂无简介" }}</p>

      <div class="chips" v-if="competition.tags?.length">
        <span v-for="tagItem in competition.tags" :key="tagItem" class="chip">
          {{ tagItem }}
        </span>
      </div>

      <div class="detail-grid">
        <div class="detail-card">
          <div class="detail-label">主办方</div>
          <div class="detail-value">{{ competition.organizer || "未提供" }}</div>
        </div>
        <div class="detail-card">
          <div class="detail-label">报名截止</div>
          <div class="detail-value">{{ formatDate(competition.signup_end) }}</div>
        </div>
        <div class="detail-card">
          <div class="detail-label">比赛时间</div>
          <div class="detail-value">{{ formatDate(competition.event_start) }}</div>
        </div>
        <div class="detail-card">
          <div class="detail-label">地点</div>
          <div class="detail-value">{{ competition.location || "未提供" }}</div>
        </div>
      </div>

      <div class="hero-actions">
        <button class="btn btn-primary" @click="toggleFavorite">收藏</button>
      </div>

      <p v-if="message" class="message">{{ message }}</p>
    </div>
  </section>
  <section v-else class="page">
    <div class="panel">加载中...</div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { fetchCompetition } from "../api";
import { addFavorite } from "../../favorites/api";

const route = useRoute();
const competition = ref(null);
const message = ref("");

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

async function load() {
  const data = await fetchCompetition(route.params.id);
  competition.value = data;
}

async function toggleFavorite() {
  if (!competition.value) return;
  message.value = "";
  try {
    await addFavorite(competition.value.id);
    message.value = "已收藏";
  } catch (err) {
    message.value = err instanceof Error ? err.message : "收藏失败";
  }
}

onMounted(load);
</script>
