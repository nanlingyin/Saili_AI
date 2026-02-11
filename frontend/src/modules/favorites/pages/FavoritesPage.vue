<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">收藏</p>
      <h1 class="page-title">我的收藏</h1>
      <p class="page-desc">你收藏的竞赛集中展示在这里，方便随时查看。</p>
    </div>

    <div v-if="!loggedIn" class="card" style="max-width: 480px">
      <p style="margin-bottom: 16px; color: var(--secondary)">登录后查看你的收藏列表。</p>
      <router-link to="/login" class="btn btn-primary">前往登录</router-link>
    </div>

    <template v-else>
      <ul class="grid grid-2" v-if="items.length">
        <li v-for="item in items" :key="item.id" class="card">
          <router-link :to="`/competitions/${item.id}`" class="card-title">
            {{ item.title }}
          </router-link>
          <p class="card-meta">报名截止：{{ formatDate(item.signup_end) }}</p>
        </li>
      </ul>
      <p v-else class="empty">暂无收藏</p>
    </template>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";
import { fetchFavorites } from "../api";
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
    items.value = await fetchFavorites();
  } catch {
    // 未登录或网络异常
  }
}

onMounted(load);
</script>
