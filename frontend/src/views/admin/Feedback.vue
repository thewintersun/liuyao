<template>
  <div class="page admin-page">
    <div class="filter-tabs">
      <span
        v-for="tab in statusTabs"
        :key="tab.value"
        class="filter-tab"
        :class="{ active: currentStatus === tab.value }"
        @click="filterByStatus(tab.value)"
      >{{ $t(tab.label) }}</span>
    </div>

    <div class="feedback-list">
      <div
        class="feedback-item touchable"
        v-for="item in feedbacks"
        :key="item.id"
        @click="toggleExpand(item.id)"
      >
        <div class="feedback-header">
          <span class="feedback-user">{{ item.username || $t('游客') }}</span>
          <span class="feedback-status" :class="item.status">{{ statusLabel(item.status) }}</span>
        </div>
        <p class="feedback-summary">{{ expanded === item.id ? item.feedback : truncate(item.feedback) }}</p>
        <div class="feedback-meta">
          <span>{{ item.contact }}</span>
          <span>{{ item.created_at }}</span>
        </div>
        <div class="feedback-actions" v-if="expanded === item.id && item.status !== 'resolved'">
          <button
            v-if="item.status === 'unread'"
            class="action-btn-sm"
            @click.stop="markStatus(item, 'read')"
          >{{ $t('标记已读') }}</button>
          <button
            class="action-btn-sm resolve"
            @click.stop="markStatus(item, 'resolved')"
          >{{ $t('标记已处理') }}</button>
        </div>
      </div>
    </div>

    <div class="empty-tip" v-if="!loading && feedbacks.length === 0">{{ $t('暂无数据') }}</div>

    <div class="pagination" v-if="totalPages > 1">
      <button :disabled="page <= 1" @click="changePage(page - 1)">{{ $t('上一页') }}</button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="changePage(page + 1)">{{ $t('下一页') }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAdminFeedback, updateFeedbackStatus } from '../../api/index.js'
import { showToast } from '../../utils/toast.js'

const feedbacks = ref([])
const page = ref(1)
const totalPages = ref(1)
const currentStatus = ref('')
const expanded = ref(null)
const loading = ref(false)

const statusTabs = [
  { label: '全部', value: '' },
  { label: '未读', value: 'unread' },
  { label: '已读', value: 'read' },
  { label: '已处理', value: 'resolved' },
]

function statusLabel(s) {
  const map = { unread: '未读', read: '已读', resolved: '已处理' }
  return map[s] || s
}

function truncate(text) {
  return text && text.length > 60 ? text.slice(0, 60) + '...' : text
}

function toggleExpand(id) {
  expanded.value = expanded.value === id ? null : id
}

async function loadFeedback() {
  loading.value = true
  try {
    const data = await getAdminFeedback(page.value, 20, currentStatus.value)
    feedbacks.value = data.feedbacks
    totalPages.value = data.total_pages
  } catch (e) {
    console.error('加载反馈失败', e)
  } finally {
    loading.value = false
  }
}

function filterByStatus(status) {
  currentStatus.value = status
  page.value = 1
  loadFeedback()
}

function changePage(p) {
  page.value = p
  loadFeedback()
}

async function markStatus(item, status) {
  try {
    await updateFeedbackStatus(item.id, status)
    item.status = status
  } catch (e) {
    showToast('操作失败', 'error')
  }
}

onMounted(loadFeedback)
</script>

<style scoped>
.filter-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.filter-tab {
  padding: 6px 16px;
  font-size: 14px;
  color: var(--color-text-secondary);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  cursor: pointer;
}
.filter-tab.active {
  color: #141414;
  background: var(--color-primary);
  border-color: var(--color-primary);
}
.feedback-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.feedback-item {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 12px 16px;
  cursor: pointer;
}
.feedback-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.feedback-user {
  font-size: 15px;
  color: var(--color-text);
}
.feedback-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 2px;
}
.feedback-status.unread {
  background: rgba(249,212,124,0.2);
  color: var(--color-primary);
}
.feedback-status.read {
  background: rgba(136,136,136,0.2);
  color: var(--color-text-secondary);
}
.feedback-status.resolved {
  background: rgba(89,179,0,0.2);
  color: #59B300;
}
.feedback-summary {
  font-size: 14px;
  color: var(--color-text);
  line-height: 1.5;
  margin-bottom: 6px;
  word-break: break-all;
}
.feedback-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.feedback-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(249,212,124,0.1);
}
.action-btn-sm {
  height: 32px;
  padding: 0 14px;
  font-size: 13px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  border-radius: 1px;
}
.action-btn-sm.resolve {
  background: var(--color-primary);
  color: #141414;
  border-color: var(--color-primary);
}
.empty-tip {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 40px 0;
}
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}
.pagination button {
  height: 36px;
  padding: 0 16px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  color: var(--color-text);
  font-size: 14px;
  border-radius: 1px;
}
.pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.page-info {
  color: var(--color-text-secondary);
  font-size: 14px;
}
</style>
