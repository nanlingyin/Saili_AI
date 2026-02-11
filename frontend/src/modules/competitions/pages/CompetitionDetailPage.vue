<template>
  <section v-if="competition" class="page">
    <div class="page-header">
      <p class="page-overline">竞赛详情</p>
      <h1 class="page-title">{{ competition.title }}</h1>
      <p class="page-desc">{{ competition.description || "暂无简介" }}</p>
      <div class="tags" v-if="competition.tags?.length" style="margin-top: 12px">
        <span v-for="t in competition.tags" :key="t" class="tag">{{ t }}</span>
      </div>
    </div>

    <div class="detail-grid">
      <div class="detail-item">
        <div class="detail-label">主办方</div>
        <div class="detail-value">{{ competition.organizer || "未提供" }}</div>
      </div>
      <div class="detail-item">
        <div class="detail-label">报名截止</div>
        <div class="detail-value">{{ formatDate(competition.signup_end) }}</div>
      </div>
      <div class="detail-item">
        <div class="detail-label">比赛时间</div>
        <div class="detail-value">{{ formatDate(competition.event_start) }}</div>
      </div>
      <div class="detail-item">
        <div class="detail-label">地点</div>
        <div class="detail-value">{{ competition.location || "未提供" }}</div>
      </div>
      <div class="detail-item" v-if="competition.reward">
        <div class="detail-label">奖项</div>
        <div class="detail-value">{{ competition.reward }}</div>
      </div>
      <div class="detail-item" v-if="competition.requirements">
        <div class="detail-label">参赛要求</div>
        <div class="detail-value">{{ competition.requirements }}</div>
      </div>
    </div>

    <div class="btn-group">
      <button class="btn btn-primary" @click="toggleFavorite">收藏此竞赛</button>
      <router-link class="btn btn-secondary" to="/competitions">返回列表</router-link>
    </div>

    <div v-if="message" class="msg" :class="msgClass">{{ message }}</div>
  </section>
  <section v-else class="page">
    <p class="empty">加载中...</p>
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
const msgClass = ref("msg-success");

function formatDate(value) {
  if (!value) return "--";
  return new Date(value).toLocaleDateString("zh-CN");
}

async function load() {
  competition.value = await fetchCompetition(route.params.id);
}

async function toggleFavorite() {
  if (!competition.value) return;
  message.value = "";
  try {
    await addFavorite(competition.value.id);
    message.value = "已收藏";
    msgClass.value = "msg-success";
  } catch (err) {
    message.value = err instanceof Error ? err.message : "操作失败";
    msgClass.value = "msg-error";
  }
}

onMounted(load);
</script>
