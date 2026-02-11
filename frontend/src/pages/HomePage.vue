<template>
  <section class="page">
    <div class="hero">
      <p class="page-overline">竞赛智能平台</p>
      <h1 class="page-title">发现适合你的竞赛</h1>
      <p class="page-desc">
        聚合校内外竞赛信息，结合你的专业与兴趣智能推荐，帮你把握每一个值得参与的机会。
      </p>
      <div class="btn-group">
        <router-link class="btn btn-primary" to="/competitions">浏览竞赛</router-link>
        <router-link v-if="!loggedIn" class="btn btn-secondary" to="/register">免费注册</router-link>
        <router-link v-else class="btn btn-secondary" to="/recommendations">查看推荐</router-link>
      </div>
    </div>

    <div class="features-grid">
      <div class="feature-card">
        <div class="feature-icon">01</div>
        <h3 class="feature-title">竞赛聚合</h3>
        <p class="feature-desc">
          整合多渠道竞赛数据，统一格式与审核流程，支持关键词与标签筛选。
        </p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">02</div>
        <h3 class="feature-title">智能推荐</h3>
        <p class="feature-desc">
          根据你的专业、兴趣与订阅偏好，自动匹配并推荐最相关的竞赛。
        </p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">03</div>
        <h3 class="feature-title">收藏与提醒</h3>
        <p class="feature-desc">
          一键收藏感兴趣的竞赛，报名截止前自动发送邮件提醒，不再错过。
        </p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { useAuth } from "../core/auth-store";

const { loggedIn } = useAuth();
</script>
