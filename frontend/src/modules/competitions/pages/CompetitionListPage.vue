<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">竞赛库</p>
      <h1 class="page-title">竞赛列表</h1>
      <p class="page-desc">按关键词与标签筛选已发布的竞赛信息。共 {{ total }} 项竞赛。</p>
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
        <button class="btn btn-primary btn-sm" @click="search">搜索</button>
      </div>
    </div>

    <ul class="grid grid-2">
      <li v-for="item in items" :key="item.id" class="card">
        <router-link :to="`/competitions/${item.id}`" class="card-title">
          {{ item.title }}
        </router-link>
        <p class="card-meta" v-if="item.description">{{ truncate(item.description, 100) }}</p>
        <p class="card-meta" v-if="item.organizer">主办方：{{ item.organizer }}</p>
        <p class="card-meta" v-if="item.signup_end">报名截止：{{ formatDate(item.signup_end) }}</p>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px">
          <span v-for="t in item.tags" :key="t" class="tag">{{ t }}</span>
          <span v-if="item.crawl_status" class="tag">{{ item.crawl_status }}</span>
          <a v-if="item.url" :href="item.url" target="_blank" rel="noopener" class="card-meta"
            style="color:var(--color-primary)">官网 ↗</a>
        </div>
      </li>
    </ul>

    <p v-if="!items.length && !loading" class="empty">暂无竞赛数据</p>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button class="btn btn-secondary btn-sm" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
      <template v-for="p in visiblePages" :key="p">
        <button v-if="p === '...'" class="btn btn-sm" disabled>…</button>
        <button v-else class="btn btn-sm" :class="p === page ? 'btn-primary' : 'btn-secondary'" @click="goPage(p)">{{ p }}</button>
      </template>
      <button class="btn btn-secondary btn-sm" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { fetchCompetitions } from "../api";

const items = ref([]);
const query = ref("");
const tag = ref("");
const page = ref(1);
const pageSize = 20;
const total = ref(0);
const loading = ref(false);

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)));

const visiblePages = computed(() => {
  const tp = totalPages.value;
  if (tp <= 7) return Array.from({ length: tp }, (_, i) => i + 1);
  const pages = [];
  const p = page.value;
  pages.push(1);
  if (p > 3) pages.push("...");
  for (let i = Math.max(2, p - 1); i <= Math.min(tp - 1, p + 1); i++) pages.push(i);
  if (p < tp - 2) pages.push("...");
  pages.push(tp);
  return pages;
});

function formatDate(value) {
  if (!value) return "";
  return new Date(value).toLocaleDateString("zh-CN");
}

function truncate(text, max) {
  if (!text) return "";
  return text.length > max ? text.slice(0, max) + "..." : text;
}

async function load() {
  loading.value = true;
  try {
    const data = await fetchCompetitions({
      q: query.value || undefined,
      tag: tag.value || undefined,
      page: page.value,
      page_size: pageSize,
    });
    items.value = data.items || [];
    total.value = data.total || 0;
  } finally {
    loading.value = false;
  }
}

function search() {
  page.value = 1;
  load();
}

function goPage(p) {
  if (p < 1 || p > totalPages.value) return;
  page.value = p;
  load();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

onMounted(load);
</script>

<style scoped>
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  flex-wrap: wrap;
}
</style>
