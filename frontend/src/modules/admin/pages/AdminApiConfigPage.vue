<template>
  <section class="page">
    <div class="panel">
      <p class="eyebrow">配置中心</p>
      <h1 class="page-title">API 配置</h1>
      <p class="page-subtitle">读取与修改 YAML 配置（管理员）。</p>
    </div>

    <div class="panel">
      <h2 class="section-title">AI 抽取配置</h2>
      <form class="form-grid" @submit.prevent="save">
        <label class="field">
          <span>启用 AI 抽取</span>
          <select v-model="form.providers.ai_extraction.enabled" class="input">
            <option :value="true">启用</option>
            <option :value="false">关闭</option>
          </select>
        </label>
        <label class="field">
          <span>API 地址</span>
          <input v-model="form.providers.ai_extraction.base_url" class="input" />
        </label>
        <label class="field">
          <span>模型名</span>
          <input v-model="form.providers.ai_extraction.model" class="input" />
        </label>
        <label class="field">
          <span>API Key（留空保持不变）</span>
          <input v-model="form.providers.ai_extraction.api_key" class="input" />
        </label>
        <label class="field">
          <span>超时（秒）</span>
          <input v-model.number="form.providers.ai_extraction.timeout_seconds" class="input" type="number" min="1" />
        </label>

        <h2 class="section-title">入库配置</h2>
        <label class="field">
          <span>主源文件路径</span>
          <input v-model="form.providers.ingestion.stable_source_path" class="input" />
        </label>
        <label class="field">
          <span>兜底文件路径</span>
          <input v-model="form.providers.ingestion.fallback_source_path" class="input" />
        </label>
        <label class="field">
          <span>失败阈值</span>
          <input v-model.number="form.providers.ingestion.failure_threshold" class="input" type="number" min="1" />
        </label>
        <label class="field">
          <span>调度间隔（秒）</span>
          <input v-model.number="form.providers.ingestion.interval_seconds" class="input" type="number" min="1" />
        </label>

        <h2 class="section-title">鉴权配置</h2>
        <label class="field">
          <span>JWT 过期时间（分钟）</span>
          <input v-model.number="form.providers.auth.access_token_expire_minutes" class="input" type="number" min="1" />
        </label>

        <div class="hero-actions">
          <button class="btn btn-ghost" type="button" @click="load">重新加载</button>
          <button class="btn btn-primary" type="submit">保存配置</button>
        </div>
      </form>

      <p v-if="message" class="message">{{ message }}</p>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";

import { fetchApiProviders, updateApiProviders } from "../api";

const message = ref("");
const form = reactive({
  version: 1,
  providers: {
    ai_extraction: {
      enabled: false,
      base_url: "",
      model: "",
      api_key: "",
      timeout_seconds: 15,
    },
    ingestion: {
      stable_source_path: "",
      fallback_source_path: "",
      failure_threshold: 3,
      interval_seconds: 900,
    },
    auth: {
      access_token_expire_minutes: 120,
    },
  },
});

function applyConfig(payload) {
  form.version = payload.version ?? 1;
  form.providers.ai_extraction.enabled = Boolean(payload.providers.ai_extraction.enabled);
  form.providers.ai_extraction.base_url = payload.providers.ai_extraction.base_url ?? "";
  form.providers.ai_extraction.model = payload.providers.ai_extraction.model ?? "";
  form.providers.ai_extraction.api_key = payload.providers.ai_extraction.api_key ?? "";
  form.providers.ai_extraction.timeout_seconds = payload.providers.ai_extraction.timeout_seconds ?? 15;
  form.providers.ingestion.stable_source_path = payload.providers.ingestion.stable_source_path ?? "";
  form.providers.ingestion.fallback_source_path = payload.providers.ingestion.fallback_source_path ?? "";
  form.providers.ingestion.failure_threshold = payload.providers.ingestion.failure_threshold ?? 3;
  form.providers.ingestion.interval_seconds = payload.providers.ingestion.interval_seconds ?? 900;
  form.providers.auth.access_token_expire_minutes = payload.providers.auth.access_token_expire_minutes ?? 120;
}

async function load() {
  message.value = "";
  try {
    const data = await fetchApiProviders();
    applyConfig(data);
  } catch (err) {
    message.value = err instanceof Error ? err.message : "加载配置失败";
  }
}

async function save() {
  message.value = "";
  try {
    const payload = JSON.parse(JSON.stringify(form));
    const saved = await updateApiProviders(payload);
    applyConfig(saved);
    message.value = "配置已保存";
  } catch (err) {
    message.value = err instanceof Error ? err.message : "保存失败";
  }
}

onMounted(load);
</script>
