<template>
  <section class="page">
    <div class="panel">
      <p class="eyebrow">账户</p>
      <h1 class="page-title">登录</h1>
      <p class="page-subtitle">使用账号进入系统，访问收藏、订阅与后台。</p>

      <form @submit.prevent="handleLogin" class="form-grid">
        <label class="field">
          <span>用户名</span>
          <input v-model="form.username" class="input" required />
        </label>
        <label class="field">
          <span>密码</span>
          <input v-model="form.password" class="input" type="password" required />
        </label>
        <button class="btn btn-primary" type="submit">登录</button>
      </form>

      <p v-if="error" class="message message-error">{{ error }}</p>
      <p v-if="success" class="message">{{ success }}</p>
    </div>
  </section>
</template>

<script setup>
import { reactive, ref } from "vue";

import { login } from "../api";

const form = reactive({
  username: "",
  password: "",
});

const error = ref("");
const success = ref("");

async function handleLogin() {
  error.value = "";
  success.value = "";
  try {
    const data = await login(form);
    localStorage.setItem("auth_token", data.access_token);
    localStorage.setItem("auth_user", JSON.stringify(data));
    success.value = "登录成功";
  } catch (err) {
    error.value = err instanceof Error ? err.message : "登录失败";
  }
}
</script>
