<template>
  <div class="tabbar" v-if="showTabBar">
    <div
      v-for="tab in tabs"
      :key="tab.path"
      class="tabbar-item"
      :class="{ active: currentTab === tab.key }"
      @click="$router.push(tab.path)"
    >
      <span class="tabbar-icon">{{ tab.icon }}</span>
      <span class="tabbar-label">{{ tab.label }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { t } from '../utils/locale.js'

const route = useRoute()

const tabs = computed(() => [
  { key: 'qigua', path: '/', label: t('起卦'), icon: '📖' },
  { key: 'records', path: '/records', label: t('记录'), icon: '📋' },
  { key: 'settings', path: '/settings', label: t('设置'), icon: '⚙' },
])

const showTabBar = computed(() => true)
const currentTab = computed(() => route.meta.tab || 'qigua')
</script>

<style scoped>
.tabbar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 480px;
  height: 56px;
  background-color: var(--color-card);
  border-top: 1px solid var(--color-border);
  display: flex;
  z-index: 100;
}
.tabbar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: color 0.2s;
}
.tabbar-item.active {
  color: var(--color-primary);
}
.tabbar-icon {
  font-size: 20px;
  margin-bottom: 2px;
}
.tabbar-label {
  font-size: 12px;
}

@media (min-width: 768px) {
  .tabbar {
    max-width: 640px;
  }
}
@media (min-width: 1200px) {
  .tabbar {
    max-width: 768px;
  }
}
</style>
