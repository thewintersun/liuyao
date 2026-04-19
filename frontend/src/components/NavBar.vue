<template>
  <div class="navbar" v-if="showNavBar">
    <button class="navbar-back" @click="goBack">&#8249; {{ $t('返回') }}</button>
    <span class="navbar-title">{{ $t(title) }}</span>
    <span class="navbar-placeholder"></span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { t } from '../utils/locale.js'

const route = useRoute()
const router = useRouter()

const tabRoots = ['/', '/records', '/settings']
const showNavBar = computed(() => !tabRoots.includes(route.path))

const titleMap = {
  '/yao-input': '起卦',
  '/hexagram': '六爻排盘',
  '/category': '所问事宜类别选择',
  '/analysis': '解卦',
  '/chat': '解卦对话',
  '/guide': '起卦必读',
  '/disclaimer': '免责声明',
  '/feedback': '建议反馈',
  '/login': '登录',
  '/forgot-password': '找回密码',
  '/reset-password': '重置密码',
  '/account': '账户',
  '/invite': '邀请好友',
  '/admin': '后台管理',
  '/admin/users': '用户管理',
  '/admin/config': '系统设置',
  '/admin/prompts': '提示词管理',
  '/admin/feedback': '反馈管理',
  '/admin/logs': '使用日志',
}

const title = computed(() => {
  if (route.path.startsWith('/admin/users/')) return '用户详情'
  if (route.path.startsWith('/admin/logs/session/')) return '会话详情'
  return titleMap[route.path] || ''
})

function goBack() {
  router.back()
}
</script>

<style scoped>
.navbar {
  height: 44px;
  background-color: var(--color-card);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 12px;
  position: sticky;
  top: 0;
  z-index: 50;
}
.navbar-back {
  color: var(--color-primary);
  background: none;
  font-size: 16px;
  min-width: 60px;
  text-align: left;
}
.navbar-title {
  flex: 1;
  text-align: center;
  color: var(--color-text);
  font-size: 18px;
  font-weight: 500;
}
.navbar-placeholder {
  min-width: 60px;
}
</style>
