<template>
  <div class="page admin-page">
    <div class="stats-grid">
      <div class="stat-card" v-for="stat in stats" :key="stat.label">
        <div class="stat-value">{{ stat.value }}</div>
        <div class="stat-label">{{ $t(stat.label) }}</div>
      </div>
    </div>

    <div class="menu-list">
      <div class="menu-item" @click="$router.push('/admin/users')">
        <span class="menu-title">{{ $t('用户管理') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/admin/config')">
        <span class="menu-title">{{ $t('系统设置') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/admin/prompts')">
        <span class="menu-title">{{ $t('提示词管理') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/admin/feedback')">
        <span class="menu-title">{{ $t('反馈管理') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/admin/logs')">
        <span class="menu-title">{{ $t('使用日志') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAdminDashboard } from '../../api/index.js'

const stats = ref([
  { label: '总用户数', value: '-' },
  { label: '今日新增', value: '-' },
  { label: '总解卦数', value: '-' },
  { label: '今日解卦', value: '-' },
])

onMounted(async () => {
  try {
    const data = await getAdminDashboard()
    stats.value = [
      { label: '总用户数', value: data.total_users },
      { label: '今日新增', value: data.today_users },
      { label: '总解卦数', value: data.total_divinations },
      { label: '今日解卦', value: data.today_divinations },
      { label: '活跃会话', value: data.active_sessions },
    ]
  } catch (e) {
    console.error('获取看板数据失败', e)
  }
})
</script>

<style scoped>
.stats-grid {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}
.stat-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 10px 4px;
  text-align: center;
  flex: 1;
  min-width: 0;
}
.stat-value {
  font-size: 20px;
  color: var(--color-primary);
  font-weight: bold;
}
.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}
.menu-list {
  margin-top: 8px;
}
.menu-item {
  display: flex;
  align-items: center;
  height: 60px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  margin-bottom: 8px;
  padding: 0 16px;
  cursor: pointer;
}
.menu-title {
  flex: 1;
  color: var(--color-text);
  font-size: 16px;
}
.menu-arrow {
  color: var(--color-text-secondary);
  font-size: 20px;
}
</style>
