<template>
  <div class="auth-page">
    <div class="card auth-card">
      <div class="page-header">
        <p class="page-overline">账户</p>
        <h1 class="page-title">登录</h1>
        <p class="page-desc">登录后访问收藏、推荐与个人中心。</p>
      </div>

      <form @submit.prevent="handleLogin" class="form" style="margin-top: 24px">
        <label class="field">
          <span class="field-label">用户名</span>
          <input v-model="form.username" class="input" required />
        </label>
        <label class="field">
          <span class="field-label">密码</span>
          <input v-model="form.password" class="input" type="password" required />
        </label>
        <button class="btn btn-primary" type="submit" style="width:100%">登录</button>
      </form>

      <div v-if="error" class="msg msg-error" style="margin-top: 16px">{{ error }}</div>
      <div v-if="success" class="msg msg-success" style="margin-top: 16px">{{ success }}</div>

      <p class="auth-footer">
        没有账号？<router-link to="/register">注册</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { login as apiLogin } from "../api";
import { useAuth } from "../../../core/auth-store";

const router = useRouter();
const { login } = useAuth();

const form = reactive({ username: "", password: "" });
const error = ref("");
const success = ref("");

async function handleLogin() {
  error.value = "";
  success.value = "";
  try {
    const data = await apiLogin(form);
    login(data);
    success.value = "登录成功";
    setTimeout(() => router.push("/"), 600);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "登录失败";
  }
}
</script>
