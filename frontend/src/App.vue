<template>
  <div class="app-container">
    <div class="app-content">
      <NavBar />
      <div class="page-content">
        <router-view />
      </div>
      <TabBar />
    </div>
  </div>
</template>

<script setup>
import TabBar from './components/TabBar.vue'
import NavBar from './components/NavBar.vue'
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: var(--color-bg);
  display: flex;
  justify-content: center;
}
.app-content {
  width: 100%;
  max-width: 480px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}
.page-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 60px;
}

/* PC 端宽屏适配 */
@media (min-width: 768px) {
  .app-content {
    max-width: 640px;
  }
}
@media (min-width: 1200px) {
  .app-content {
    max-width: 768px;
  }
}
</style>
