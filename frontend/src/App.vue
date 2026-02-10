<template>
  <div class="app-shell">
    <header class="app-header glass">
      <div class="brand">
        <div class="brand-mark">SA</div>
        <div>
          <div class="brand-title">SaiLi AI</div>
          <div class="brand-subtitle">竞赛智能平台</div>
        </div>
      </div>
      <nav class="nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          active-class="is-active"
        >
          {{ item.label }}
        </router-link>
      </nav>
      <div class="nav-meta">
        <span class="status-dot"></span>
        <span>本地预览</span>
      </div>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { getMenuItems } from "./menu";

const menuItems = computed(() => getMenuItems());
</script>
