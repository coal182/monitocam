<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()

const logout = () => {
  authStore.logout()
  window.location.href = '/login'
}
</script>

<template>
  <div class="app">
    <nav v-if="authStore.username" class="navbar">
      <div class="nav-brand">MonitoCam</div>
      <div class="nav-links">
        <RouterLink to="/">Camaras</RouterLink>
        <RouterLink to="/recordings">Grabaciones</RouterLink>
      </div>
      <div class="nav-user">
        <span>{{ authStore.username }}</span>
        <button @click="logout">Logout</button>
      </div>
    </nav>
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  background: #f5f5f5;
}

.navbar {
  background: #1a1a2e;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-links a {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  background: #16213e;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-user button {
  background: #e94560;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.nav-user button:hover {
  background: #d63650;
}

.main-content {
  padding: 2rem;
}
</style>
