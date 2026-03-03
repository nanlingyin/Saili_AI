<template>
  <section class="page">
    <div class="panel">
      <p class="eyebrow">演示</p>
      <h1 class="page-title">示例模块</h1>
      <p v-if="error" class="message message-error">{{ error }}</p>
      <p v-else class="page-subtitle">{{ message }}</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from "vue";

import { useSampleApi } from "../api";

const { fetchHello } = useSampleApi();
const message = ref("加载中...");
const error = ref("");

onMounted(async () => {
  try {
    const data = await fetchHello();
    message.value = data.message ?? "获取成功";
  } catch (err) {
    error.value = err instanceof Error ? err.message : "请求失败";
  }
});
</script>
