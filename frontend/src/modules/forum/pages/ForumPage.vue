<template>
  <section class="page">
    <div class="page-header">
      <p class="page-overline">论坛</p>
      <h1 class="page-title">校园论坛</h1>
      <p class="page-desc">按学校分区交流；学校管理员和学生管理员可置顶/删除管理内容。</p>
    </div>

    <div v-if="!loggedIn" class="card" style="max-width: 480px">
      <p style="margin-bottom: 16px; color: var(--secondary)">登录后访问校园论坛。</p>
      <router-link to="/login" class="btn btn-primary">前往登录</router-link>
    </div>

    <template v-else>
      <div class="card" style="max-width: 760px;">
        <h2 class="section-title">发布帖子</h2>
        <p class="card-meta" style="margin-bottom: 12px">示例：标题“2026数学建模校赛组队”，正文里写时间地点与群号说明。</p>
        <form @submit.prevent="handleCreatePost" class="form form-wide">
          <label class="field">
            <span class="field-label">标题</span>
            <input v-model="postForm.title" class="input" placeholder="示例：ACM 校队招新答疑" />
          </label>
          <label class="field">
            <span class="field-label">内容</span>
            <textarea v-model="postForm.content" class="input" rows="4" placeholder="示例：本周三晚 19:00 线上答疑，群号 123456789"></textarea>
          </label>
          <button class="btn btn-primary" type="submit">发布帖子</button>
        </form>
      </div>

      <div v-if="message" class="msg" :class="msgClass">{{ message }}</div>

      <div class="card">
        <h2 class="section-title">帖子列表</h2>
        <ul class="grid" v-if="items.length">
          <li v-for="post in items" :key="post.id" class="card">
            <div class="card-row">
              <div>
                <div class="card-title">
                  <span v-if="post.pinned">📌 </span>{{ post.title }}
                </div>
                <p class="card-meta">学校：{{ post.school }} ｜ 作者：{{ post.author_username }}</p>
                <p class="card-meta" style="margin-top: 6px">{{ post.content }}</p>
              </div>
              <div class="btn-group" v-if="isSchoolManager">
                <button class="btn btn-secondary btn-sm" @click="togglePin(post.id)">置顶/取消</button>
                <button class="btn btn-secondary btn-sm" @click="removePost(post.id)">删除</button>
              </div>
            </div>

            <div class="divider"></div>
            <div class="form form-wide" style="gap:10px; max-width:none;">
              <label class="field">
                <span class="field-label">回复</span>
                <input v-model="replyDraft[post.id]" class="input" placeholder="示例：我已进群，明天见" />
              </label>
              <div class="btn-group">
                <button class="btn btn-primary btn-sm" @click="handleReply(post.id)">发送回复</button>
              </div>
            </div>

            <ul class="grid" v-if="post.replies?.length" style="margin-top: 12px;">
              <li v-for="reply in post.replies" :key="reply.id" class="card card-row">
                <div>
                  <p class="card-meta">{{ reply.author_username }}：{{ reply.content }}</p>
                </div>
                <button
                  v-if="isSchoolManager"
                  class="btn btn-secondary btn-sm"
                  @click="removeReply(post.id, reply.id)"
                >删除</button>
              </li>
            </ul>
          </li>
        </ul>
        <p v-else class="empty">暂无帖子</p>
      </div>
    </template>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";

import { useAuth } from "../../../core/auth-store";
import { useForumApi } from "../api";

const {
  fetchForumPosts,
  fetchForumPost,
  createForumPost,
  createForumReply,
  togglePinPost,
  deleteForumPost,
  deleteForumReply,
} = useForumApi();

const { loggedIn, isSchoolManager } = useAuth();

const items = ref([]);
const message = ref("");
const msgClass = ref("msg-success");
const replyDraft = reactive({});

const postForm = reactive({
  title: "",
  content: "",
});

async function load() {
  if (!loggedIn.value) return;
  const data = await fetchForumPosts({ page: 1, page_size: 20 });
  items.value = data.items || [];

  for (const post of items.value) {
    const detail = await fetchForumPost(post.id);
    post.replies = detail.replies || [];
  }
}

async function handleCreatePost() {
  message.value = "";
  try {
    await createForumPost({ title: postForm.title, content: postForm.content });
    postForm.title = "";
    postForm.content = "";
    message.value = "帖子已发布";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "发布失败";
    msgClass.value = "msg-error";
  }
}

async function handleReply(postId) {
  message.value = "";
  const content = (replyDraft[postId] || "").trim();
  if (!content) {
    message.value = "请输入回复内容";
    msgClass.value = "msg-error";
    return;
  }

  try {
    await createForumReply(postId, { content });
    replyDraft[postId] = "";
    message.value = "回复已发送";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "回复失败";
    msgClass.value = "msg-error";
  }
}

async function togglePin(postId) {
  message.value = "";
  try {
    await togglePinPost(postId);
    message.value = "已更新置顶状态";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "操作失败";
    msgClass.value = "msg-error";
  }
}

async function removePost(postId) {
  message.value = "";
  try {
    await deleteForumPost(postId);
    message.value = "帖子已删除";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "删除失败";
    msgClass.value = "msg-error";
  }
}

async function removeReply(postId, replyId) {
  message.value = "";
  try {
    await deleteForumReply(replyId);
    message.value = "回复已删除";
    msgClass.value = "msg-success";
    await load();
  } catch (err) {
    message.value = err instanceof Error ? err.message : "删除失败";
    msgClass.value = "msg-error";
  }
}

onMounted(load);
</script>
