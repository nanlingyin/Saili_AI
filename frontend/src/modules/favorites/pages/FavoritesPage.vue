<template>
  <section class="page">
    <div class="panel">
      <p class="eyebrow">收藏</p>
      <h1 class="page-title">我的收藏</h1>
      <p class="page-subtitle">你已收藏的竞赛会集中显示在这里。</p>
    </div>

    <ul class="list-grid cols-2">
      <li v-for="item in items" :key="item.id" class="card">
        <router-link :to="`/competitions/${item.id}`" class="card-title">
          {{ item.title }}
        </router-link>
        <p class="card-meta">报名截止：{{ formatDate(item.signup_end) }}</p>
      </li>
    </ul>

    <p v-if="!items.length" class="empty">暂无收藏</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";

import { fetchFavorites } from "../api";

const items = ref([]);

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

async function load() {
  items.value = await fetchFavorites();
}

onMounted(load);
</script>
