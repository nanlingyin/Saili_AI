<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">智能匹配</p>
      <h1 class="page-title">专业 × 竞赛 智能推荐</h1>
      <p class="page-desc">输入你的专业，AI 将基于语义相似度、领域关键词和 TF-IDF 算法为你匹配最合适的竞赛。</p>
    </div>

    <div class="card">
      <form class="filters" @submit.prevent="handleMatch">
        <label class="field" style="flex:1">
          <span class="field-label">你的专业</span>
          <input v-model="major" class="input" placeholder="例如：计算机科学与技术、金融学、机械工程" required />
        </label>
        <label class="field">
          <span class="field-label">返回数量</span>
          <select v-model.number="topK" class="input">
            <option :value="5">5</option>
            <option :value="8">8</option>
            <option :value="12">12</option>
            <option :value="20">20</option>
          </select>
        </label>
        <button class="btn btn-primary btn-sm" type="submit" :disabled="loading">
          {{ loading ? '匹配中...' : '开始匹配' }}
        </button>
      </form>
    </div>

    <div v-if="error" class="msg msg-error">{{ error }}</div>

    <div v-if="matches.length" class="card" style="margin-top:8px">
      <h2 class="section-title">匹配结果（{{ matchedMajor }}）</h2>
      <ul class="grid grid-2">
        <li v-for="item in matches" :key="item.id" class="card">
          <div style="display:flex;justify-content:space-between;align-items:start">
            <router-link :to="`/competitions/${item.id}`" class="card-title">
              {{ item.name }}
            </router-link>
            <span class="tag" :class="scoreClass(item.score)">{{ item.score }}分</span>
          </div>
          <p class="card-meta" v-if="item.reason">💡 {{ item.reason }}</p>
          <p class="card-meta" v-if="item.intro">{{ truncate(item.intro, 120) }}</p>
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px">
            <span class="tag" v-if="item.crawl_status">{{ item.crawl_status }}</span>
            <span class="card-meta" v-if="item.deadline_date">截止：{{ item.deadline_date }}</span>
            <a v-if="item.url" :href="item.url" target="_blank" rel="noopener" class="card-meta"
              style="color:var(--color-primary)">官网 ↗</a>
          </div>
        </li>
      </ul>
    </div>

    <p v-if="searched && !matches.length && !loading" class="empty">未找到匹配的竞赛，请尝试其他专业名称。</p>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { matchByMajor } from "../api";

const major = ref("");
const topK = ref(8);
const matches = ref([]);
const matchedMajor = ref("");
const loading = ref(false);
const searched = ref(false);
const error = ref("");

function truncate(text, max) {
  if (!text) return "";
  return text.length > max ? text.slice(0, max) + "..." : text;
}

function scoreClass(score) {
  if (score >= 60) return "tag-high";
  if (score >= 30) return "tag-mid";
  return "";
}

async function handleMatch() {
  if (!major.value.trim()) return;
  loading.value = true;
  error.value = "";
  searched.value = true;
  try {
    const data = await matchByMajor(major.value.trim(), topK.value);
    matches.value = data.matches || [];
    matchedMajor.value = data.major || major.value;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "匹配失败";
    matches.value = [];
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.tag-high {
  background: var(--color-success, #22c55e);
  color: #fff;
}
.tag-mid {
  background: var(--color-warning, #f59e0b);
  color: #fff;
}
</style>
