<template>
  <div>
    <nav class="site-nav">
      <div class="site-nav-inner">
        <router-link to="/" class="nav-brand">
          <div class="nav-logo">SL</div>
          <span>SaiLi AI</span>
        </router-link>
        <div class="nav-links">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="nav-link"
            active-class="is-active"
            exact-active-class=""
          >
            {{ item.label }}
          </router-link>
        </div>
        <div class="nav-right">
          <template v-if="loggedIn">
            <span class="nav-username">{{ username }}</span>
            <button class="nav-btn-logout" @click="handleLogout">退出</button>
          </template>
        </div>
      </div>
    </nav>
    <main class="site-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { getMenuItems } from "./menu";
import { useAuth } from "./core/auth-store";

const router = useRouter();
const { loggedIn, username, logout } = useAuth();
const menuItems = computed(() => getMenuItems());

function handleLogout() {
  logout();
  router.push("/");
}
</script>
