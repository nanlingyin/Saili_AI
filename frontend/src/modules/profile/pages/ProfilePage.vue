<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">个人中心</p>
      <h1 class="page-title">我的资料</h1>
      <p class="page-desc">完善学业与兴趣信息，系统将据此为你推荐更匹配的竞赛。</p>
    </div>

    <div v-if="!loggedIn" class="card" style="max-width: 480px">
      <p style="margin-bottom: 16px; color: var(--secondary)">登录后即可编辑个人资料。</p>
      <router-link to="/login" class="btn btn-primary">前往登录</router-link>
    </div>

    <div v-else class="card" style="max-width: 560px">
      <form @submit.prevent="handleSave" class="form form-wide">
        <label class="field">
          <span class="field-label">大学</span>
          <input v-model="form.university" class="input" placeholder="如：北京大学" />
        </label>
        <label class="field">
          <span class="field-label">专业</span>
          <input v-model="form.major" class="input" placeholder="如：计算机科学与技术" />
        </label>
        <label class="field">
          <span class="field-label">年级</span>
          <input v-model="form.grade" class="input" placeholder="如：大二" />
        </label>
        <label class="field">
          <span class="field-label">兴趣标签</span>
          <input v-model="tagsInput" class="input" placeholder="用逗号分隔，如：编程, 数学建模, 英语" />
        </label>
        <label class="field">
          <span class="field-label">个人简介</span>
          <textarea v-model="form.bio" class="input" rows="3" placeholder="简单介绍一下自己"></textarea>
        </label>
        <button class="btn btn-primary" type="submit">保存</button>
      </form>

      <div v-if="error" class="msg msg-error" style="margin-top: 16px">{{ error }}</div>
      <div v-if="success" class="msg msg-success" style="margin-top: 16px">{{ success }}</div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { getProfile, updateProfile } from "../api";
import { useAuth } from "../../../core/auth-store";

const { loggedIn } = useAuth();

const form = reactive({
  university: "",
  major: "",
  grade: "",
  interest_tags: [],
  bio: "",
});

const tagsInput = computed({
  get: () => form.interest_tags.join(", "),
  set: (val) => {
    form.interest_tags = val.split(",").map((t) => t.trim()).filter(Boolean);
  },
});

const error = ref("");
const success = ref("");

onMounted(async () => {
  if (!loggedIn.value) return;
  try {
    const data = await getProfile();
    form.university = data.university || "";
    form.major = data.major || "";
    form.grade = data.grade || "";
    form.interest_tags = data.interest_tags || [];
    form.bio = data.bio || "";
  } catch {
    // 首次访问无数据，忽略
  }
});

async function handleSave() {
  error.value = "";
  success.value = "";
  try {
    const data = await updateProfile({
      university: form.university,
      major: form.major,
      grade: form.grade,
      interest_tags: form.interest_tags,
      bio: form.bio,
    });
    form.university = data.university;
    form.major = data.major;
    form.grade = data.grade;
    form.interest_tags = data.interest_tags;
    form.bio = data.bio;
    success.value = "保存成功";
  } catch (err) {
    error.value = err instanceof Error ? err.message : "保存失败";
  }
}
</script>
