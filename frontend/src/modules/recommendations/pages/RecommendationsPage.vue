<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">推荐</p>
      <h1 class="page-title">推荐竞赛</h1>
      <p class="page-desc">根据你的专业、兴趣与订阅偏好，为你筛选最相关的竞赛。</p>
    </div>

    <div v-if="!loggedIn" class="card" style="max-width: 480px">
      <p style="margin-bottom: 16px; color: var(--secondary)">登录并完善个人资料后，即可获取个性化推荐。</p>
      <div class="btn-group">
        <router-link to="/login" class="btn btn-primary">前往登录</router-link>
        <router-link to="/register" class="btn btn-secondary">注册账号</router-link>
      </div>
    </div>

    <template v-else>
      <ul class="grid grid-2" v-if="items.length">
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
      <div v-else class="empty">
        <p>暂无推荐</p>
        <p style="margin-top: 8px; font-size: 13px">前往<router-link to="/profile">个人资料</router-link>完善兴趣标签，获取更精准的推荐。</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { fetchRecommendations } from "../api";
import { useAuth } from "../../../core/auth-store";

const { loggedIn } = useAuth();
const items = ref([]);

function formatDate(value) {
  if (!value) return "--";
  return new Date(value).toLocaleDateString("zh-CN");
}

async function load() {
  if (!loggedIn.value) return;
  try {
    items.value = await fetchRecommendations();
  } catch {
    // 网络异常
  }
}

onMounted(load);
</script>
