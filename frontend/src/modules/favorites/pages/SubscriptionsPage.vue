<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">订阅</p>
      <h1 class="page-title">我的订阅</h1>
      <p class="page-desc">按标签或竞赛订阅，后续可用于推荐和提醒。</p>
    </div>

    <div v-if="!loggedIn" class="card" style="max-width: 480px">
      <p style="margin-bottom: 16px; color: var(--secondary)">登录后管理你的订阅。</p>
      <router-link to="/login" class="btn btn-primary">前往登录</router-link>
    </div>

    <template v-else>
      <div class="card" style="max-width: 560px; margin-bottom: 16px">
        <form @submit.prevent="handleAdd" class="form form-wide">
          <label class="field">
            <span class="field-label">订阅类型</span>
            <select v-model="form.subscription_type" class="input">
              <option value="tag">标签（tag）</option>
              <option value="competition">竞赛（competition）</option>
            </select>
          </label>
          <label class="field">
            <span class="field-label">目标</span>
            <input
              v-model="form.target"
              class="input"
              :placeholder="form.subscription_type === 'tag' ? '如：编程' : '请输入竞赛ID，如：12'"
            />
          </label>
          <button class="btn btn-primary" type="submit">新增订阅</button>
        </form>
      </div>

      <div v-if="message" class="msg" :class="msgClass" style="margin-bottom: 16px">{{ message }}</div>

      <div class="card">
        <h2 class="section-title">当前订阅</h2>
        <ul class="grid" v-if="items.length">
          <li v-for="item in items" :key="`${item.subscription_type}:${item.target}`" class="card card-row">
            <div>
              <div class="card-title">{{ item.target }}</div>
              <p class="card-meta">类型：{{ item.subscription_type }}</p>
            </div>
            <button class="btn btn-secondary btn-sm" @click="handleRemove(item)">删除</button>
          </li>
        </ul>
        <p v-else class="empty">暂无订阅</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useFavoritesApi } from "../api";
import { useAuth } from "../../../core/auth-store";

const { fetchSubscriptions, addSubscription, removeSubscription } = useFavoritesApi();
const { loggedIn } = useAuth();

const form = reactive({
  subscription_type: "tag",
  target: "",
});

const items = ref([]);
const message = ref("");
const msgClass = ref("msg-success");

async function load() {
  if (!loggedIn.value) return;
  items.value = await fetchSubscriptions();
}

async function handleAdd() {
  message.value = "";

  const target = form.target.trim();
  if (!target) {
    message.value = "请输入订阅目标";
    msgClass.value = "msg-error";
    return;
  }

  if (form.subscription_type === "competition" && !/^\d+$/.test(target)) {
    message.value = "竞赛订阅目标必须是数字ID";
    msgClass.value = "msg-error";
    return;
  }

  try {
    await addSubscription({
      subscription_type: form.subscription_type,
      target,
    });
    form.target = "";
    message.value = "订阅已添加";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "新增订阅失败";
    msgClass.value = "msg-error";
  }
}

async function handleRemove(item) {
  message.value = "";
  try {
    await removeSubscription(item.subscription_type, item.target);
    message.value = "订阅已删除";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "删除订阅失败";
    msgClass.value = "msg-error";
  }
}

onMounted(load);
</script>
