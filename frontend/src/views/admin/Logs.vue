<template>
  <div class="page admin-page">
    <div class="filter-bar">
      <input
        v-model="filters.username"
        :placeholder="$t('用户名')"
        class="filter-input username-input"
      />
      <button class="filter-btn" @click="doFilter">{{ $t('筛选') }}</button>
    </div>
    <div class="filter-bar date-bar">
      <span class="date-label">{{ $t('从') }}</span>
      <select v-model="fromYear" class="time-sel">
        <option value="">{{ $t('年') }}</option>
        <option v-for="y in yearList" :key="'fy'+y" :value="y">{{ y }}</option>
      </select>
      <select v-model="fromMonth" class="time-sel">
        <option value="">{{ $t('月') }}</option>
        <option v-for="m in 12" :key="'fm'+m" :value="m">{{ m }}</option>
      </select>
      <select v-model="fromDay" class="time-sel">
        <option value="">{{ $t('日') }}</option>
        <option v-for="d in fromDaysInMonth" :key="'fd'+d" :value="d">{{ d }}</option>
      </select>
      <span class="date-label">{{ $t('至') }}</span>
      <select v-model="toYear" class="time-sel">
        <option value="">{{ $t('年') }}</option>
        <option v-for="y in yearList" :key="'ty'+y" :value="y">{{ y }}</option>
      </select>
      <select v-model="toMonth" class="time-sel">
        <option value="">{{ $t('月') }}</option>
        <option v-for="m in 12" :key="'tm'+m" :value="m">{{ m }}</option>
      </select>
      <select v-model="toDay" class="time-sel">
        <option value="">{{ $t('日') }}</option>
        <option v-for="d in toDaysInMonth" :key="'td'+d" :value="d">{{ d }}</option>
      </select>
    </div>

    <div class="log-list">
      <div
        class="log-item"
        :class="{ clickable: log.session_id }"
        v-for="log in logs"
        :key="log.id"
        @click="log.session_id && goDetail(log.session_id)"
      >
        <div class="log-header">
          <span class="log-user">{{ formatUser(log) }}</span>
          <span class="log-action">{{ formatAction(log) }}</span>
        </div>
        <div class="log-title" :class="{ empty: !log.title }">
          {{ log.title || $t('未记录所求之事') }}
        </div>
        <div class="log-meta">
          <span v-if="log.session_id" class="log-session">{{ log.session_id }}</span>
          <span class="log-time">{{ log.created_at }}</span>
        </div>
      </div>
    </div>

    <div class="empty-tip" v-if="!loading && logs.length === 0">{{ $t('暂无数据') }}</div>

    <div class="pagination" v-if="totalPages > 1">
      <button :disabled="page <= 1" @click="changePage(page - 1)">{{ $t('上一页') }}</button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="changePage(page + 1)">{{ $t('下一页') }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getAdminLogs } from '../../api/index.js'
import { t } from '../../utils/locale.js'

const router = useRouter()

const logs = ref([])
const page = ref(1)
const totalPages = ref(1)
const loading = ref(false)
const filters = reactive({
  username: '',
})

// 日期选择 - 起始
const fromYear = ref('')
const fromMonth = ref('')
const fromDay = ref('')

// 日期选择 - 结束
const toYear = ref('')
const toMonth = ref('')
const toDay = ref('')

const yearList = computed(() => {
  const curr = new Date().getFullYear()
  const list = []
  for (let y = curr - 5; y <= curr + 1; y++) list.push(y)
  return list
})

const fromDaysInMonth = computed(() => {
  if (!fromYear.value || !fromMonth.value) return 31
  return new Date(fromYear.value, fromMonth.value, 0).getDate()
})

const toDaysInMonth = computed(() => {
  if (!toYear.value || !toMonth.value) return 31
  return new Date(toYear.value, toMonth.value, 0).getDate()
})

// 月/年变化时自动修正日期溢出
watch([fromYear, fromMonth], () => {
  const max = fromDaysInMonth.value
  if (fromDay.value && fromDay.value > max) fromDay.value = max
})
watch([toYear, toMonth], () => {
  const max = toDaysInMonth.value
  if (toDay.value && toDay.value > max) toDay.value = max
})

function buildDateStr(y, m, d) {
  if (!y || !m || !d) return ''
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

async function loadLogs() {
  loading.value = true
  try {
    const cleanFilters = {}
    if (filters.username) cleanFilters.username = filters.username
    const dateFrom = buildDateStr(fromYear.value, fromMonth.value, fromDay.value)
    const dateTo = buildDateStr(toYear.value, toMonth.value, toDay.value)
    if (dateFrom) cleanFilters.date_from = dateFrom
    if (dateTo) cleanFilters.date_to = dateTo
    const data = await getAdminLogs(page.value, 20, cleanFilters)
    logs.value = data.logs
    totalPages.value = data.total_pages
  } catch (e) {
    console.error('加载日志失败', e)
  } finally {
    loading.value = false
  }
}

function doFilter() {
  page.value = 1
  loadLogs()
}

function changePage(p) {
  page.value = p
  loadLogs()
}

function formatUser(log) {
  if (log.username) return log.username
  if (log.user_id) return 'ID:' + log.user_id
  if (log.ip) return t('游客') + ' (' + log.ip + ')'
  return t('游客')
}

function formatAction(log) {
  const count = log.use_count || 1
  const hasReceive = log.actions && log.actions.includes('receive')
  const chatCount = count - (hasReceive ? 1 : 0)
  if (count <= 1) return hasReceive ? t('解卦') : t('追问')
  let parts = []
  if (hasReceive) parts.push(t('解卦'))
  if (chatCount > 0) parts.push(chatCount + t('次追问'))
  return parts.join(' + ')
}

function goDetail(sessionId) {
  router.push(`/admin/logs/session/${sessionId}`)
}

onMounted(loadLogs)
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.filter-bar.date-bar {
  margin-bottom: 16px;
}
.filter-input {
  height: 36px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 0 10px;
  color: var(--color-text);
  font-size: 14px;
  min-width: 0;
}
.username-input {
  flex: 1;
}
.filter-btn {
  height: 36px;
  padding: 0 14px;
  background: var(--color-primary);
  color: #141414;
  font-size: 14px;
  border-radius: 1px;
  flex: none;
}
.date-label {
  color: var(--color-text-secondary);
  font-size: 13px;
  flex: none;
}
.time-sel {
  height: 36px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 0 4px;
  color: var(--color-text);
  font-size: 13px;
  appearance: auto;
  flex: 1;
  min-width: 0;
}
.log-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.log-item {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 10px 14px;
}
.log-item.clickable {
  cursor: pointer;
}
.log-item.clickable:active {
  background: rgba(249,212,124,0.08);
}
.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.log-user {
  font-size: 14px;
  color: var(--color-text);
}
.log-action {
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(249,212,124,0.15);
  color: var(--color-primary);
  border-radius: 2px;
}
.log-title {
  font-size: 13px;
  color: var(--color-text);
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.log-title.empty {
  color: var(--color-text-secondary);
  font-style: italic;
}
.log-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.log-session {
  font-family: monospace;
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
