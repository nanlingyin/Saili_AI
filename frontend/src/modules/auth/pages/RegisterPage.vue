<template>
  <div class="auth-page">
    <div class="card auth-card">
      <div class="page-header">
        <p class="page-overline">账户</p>
        <h1 class="page-title">注册</h1>
        <p class="page-desc">创建账号，开始获取个性化竞赛推荐。</p>
      </div>

      <form @submit.prevent="handleRegister" class="form" style="margin-top: 24px">
        <label class="field">
          <span class="field-label">用户名</span>
          <input v-model="form.username" class="input" required />
        </label>
        <label class="field">
          <span class="field-label">邮箱</span>
          <input v-model="form.email" class="input" type="email" required />
        </label>
        <label class="field">
          <span class="field-label">密码</span>
          <input v-model="form.password" class="input" type="password" required />
        </label>
        <label class="field">
          <span class="field-label">确认密码</span>
          <input v-model="form.confirmPassword" class="input" type="password" required />
        </label>
        <button class="btn btn-primary" type="submit" style="width:100%">注册</button>
      </form>

      <div v-if="error" class="msg msg-error" style="margin-top: 16px">{{ error }}</div>
      <div v-if="success" class="msg msg-success" style="margin-top: 16px">{{ success }}</div>

      <p class="auth-footer">
        已有账号？<router-link to="/login">登录</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { register } from "../api";

const router = useRouter();
const form = reactive({ username: "", email: "", password: "", confirmPassword: "" });
const error = ref("");
const success = ref("");

async function handleRegister() {
  error.value = "";
  success.value = "";

  if (form.password !== form.confirmPassword) {
    error.value = "两次密码输入不一致";
    return;
  }

  try {
    await register({
      username: form.username,
      email: form.email,
      password: form.password,
    });
    success.value = "注册成功，即将跳转登录";
    setTimeout(() => router.push("/login"), 1200);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "注册失败";
  }
}
</script>
