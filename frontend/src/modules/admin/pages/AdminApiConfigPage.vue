<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">配置中心</p>
      <h1 class="page-title">系统配置与运营动作</h1>
      <p class="page-desc">管理 AI 抽取、入库、鉴权参数，并可在线调整推荐规则和触发提醒。</p>
    </div>

    <div class="card">
      <h2 class="section-title">API Providers</h2>
      <form class="form form-wide" @submit.prevent="save">
        <label class="field">
          <span class="field-label">启用 AI 抽取</span>
          <select v-model="form.providers.ai_extraction.enabled" class="input">
            <option :value="true">启用</option>
            <option :value="false">关闭</option>
          </select>
        </label>
        <label class="field">
          <span class="field-label">API 地址</span>
          <input v-model="form.providers.ai_extraction.base_url" class="input" />
        </label>
        <label class="field">
          <span class="field-label">模型名</span>
          <input v-model="form.providers.ai_extraction.model" class="input" />
        </label>
        <label class="field">
          <span class="field-label">API Key（留空保持不变）</span>
          <input v-model="form.providers.ai_extraction.api_key" class="input" />
        </label>
        <label class="field">
          <span class="field-label">超时（秒）</span>
          <input v-model.number="form.providers.ai_extraction.timeout_seconds" class="input" type="number" min="1" />
        </label>

        <hr class="divider" />

        <label class="field">
          <span class="field-label">主源文件路径</span>
          <input v-model="form.providers.ingestion.stable_source_path" class="input" />
        </label>
        <label class="field">
          <span class="field-label">兜底文件路径</span>
          <input v-model="form.providers.ingestion.fallback_source_path" class="input" />
        </label>
        <label class="field">
          <span class="field-label">失败阈值</span>
          <input v-model.number="form.providers.ingestion.failure_threshold" class="input" type="number" min="1" />
        </label>
        <label class="field">
          <span class="field-label">调度间隔（秒）</span>
          <input v-model.number="form.providers.ingestion.interval_seconds" class="input" type="number" min="1" />
        </label>

        <hr class="divider" />

        <label class="field">
          <span class="field-label">JWT 过期时间（分钟）</span>
          <input v-model.number="form.providers.auth.access_token_expire_minutes" class="input" type="number" min="1" />
        </label>

        <div class="btn-group">
          <button class="btn btn-secondary" type="button" @click="load">重新加载</button>
          <button class="btn btn-primary" type="submit">保存配置</button>
        </div>
      </form>
    </div>

    <div class="card">
      <h2 class="section-title">推荐规则权重</h2>
      <p class="section-subtitle">用于更新后端推荐规则（tag_match / deadline_soon / new_competition / major_match / interest_match）。</p>
      <form class="form form-wide" @submit.prevent="saveRules">
        <label class="field" v-for="rule in recommendationRules" :key="rule.key">
          <span class="field-label">{{ rule.key }}</span>
          <input v-model.number="rule.weight" class="input" type="number" />
        </label>
        <button class="btn btn-primary" type="submit">保存推荐权重</button>
      </form>
    </div>

    <div class="card">
      <h2 class="section-title">提醒任务</h2>
      <p class="section-subtitle">手动触发到期提醒邮件发送（需后端 SMTP 已配置）。</p>
      <button class="btn btn-secondary" @click="handleSendReminders">立即发送提醒</button>
    </div>

    <div v-if="message" class="msg" :class="msgClass">{{ message }}</div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";

import { useAdminApi } from "../api";

const { fetchApiProviders, updateApiProviders, updateRecommendationRules, sendDueReminders } = useAdminApi();
const message = ref("");
const msgClass = ref("msg-success");
const form = reactive({
  version: 1,
  providers: {
    ai_extraction: { enabled: false, base_url: "", model: "", api_key: "", timeout_seconds: 15 },
    ingestion: { stable_source_path: "", fallback_source_path: "", failure_threshold: 3, interval_seconds: 900 },
    auth: { access_token_expire_minutes: 120 },
  },
});

const recommendationRules = reactive([
  { key: "tag_match", weight: 10 },
  { key: "deadline_soon", weight: 3 },
  { key: "new_competition", weight: 2 },
  { key: "major_match", weight: 5 },
  { key: "interest_match", weight: 8 },
]);

function ok(text) {
  message.value = text;
  msgClass.value = "msg-success";
}

function fail(err, fallback) {
  message.value = err instanceof Error ? err.message : fallback;
  msgClass.value = "msg-error";
}

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
    fail(err, "加载配置失败");
  }
}

async function save() {
  message.value = "";
  try {
    const payload = JSON.parse(JSON.stringify(form));
    const saved = await updateApiProviders(payload);
    applyConfig(saved);
    ok("配置已保存");
  } catch (err) {
    fail(err, "保存配置失败");
  }
}

async function saveRules() {
  message.value = "";
  try {
    await updateRecommendationRules(
      recommendationRules.map((rule) => ({
        key: rule.key,
        weight: Number(rule.weight),
      })),
    );
    ok("推荐规则权重已更新");
  } catch (err) {
    fail(err, "保存推荐权重失败");
  }
}

async function handleSendReminders() {
  message.value = "";
  try {
    const data = await sendDueReminders();
    ok(`提醒发送完成：${data.sent} 封`);
  } catch (err) {
    fail(err, "触发提醒失败");
  }
}

onMounted(load);
</script>
