<template>
  <div class="page admin-page">
    <div class="search-bar">
      <input
        v-model="searchQuery"
        :placeholder="$t('搜索用户名')"
        class="search-input"
        @keyup.enter="doSearch"
      />
      <button class="search-btn" @click="doSearch">{{ $t('搜索') }}</button>
    </div>

    <div class="user-list">
      <div
        class="user-item"
        v-for="user in users"
        :key="user.id"
        @click="$router.push(`/admin/users/${user.id}`)"
      >
        <div class="user-info">
          <span class="user-name">{{ user.username }}</span>
          <span class="role-tag" :class="user.role">{{ roleLabel(user.role) }}</span>
        </div>
        <div class="user-meta">
          <span>{{ $t('额度') }}: {{ user.free_uses }}</span>
          <span class="user-date">{{ formatDate(user.created_at) }}</span>
        </div>
      </div>
    </div>

    <div class="empty-tip" v-if="!loading && users.length === 0">{{ $t('暂无数据') }}</div>

    <div class="pagination" v-if="totalPages > 1">
      <button :disabled="page <= 1" @click="changePage(page - 1)">{{ $t('上一页') }}</button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="changePage(page + 1)">{{ $t('下一页') }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAdminUsers } from '../../api/index.js'

const users = ref([])
const page = ref(1)
const totalPages = ref(1)
const searchQuery = ref('')
const loading = ref(false)

function roleLabel(role) {
  const map = { admin: '管理员', banned: '已封禁', user: '普通用户' }
  return map[role] || role
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return dateStr.split(' ')[0]
}

async function loadUsers() {
  loading.value = true
  try {
    const data = await getAdminUsers(page.value, 20, searchQuery.value)
    users.value = data.users
    totalPages.value = data.total_pages
  } catch (e) {
    console.error('加载用户失败', e)
  } finally {
    loading.value = false
  }
}

function doSearch() {
  page.value = 1
  loadUsers()
}

function changePage(p) {
  page.value = p
  loadUsers()
}

onMounted(loadUsers)
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.search-input {
  flex: 1;
  height: 40px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 0 12px;
  color: var(--color-text);
  font-size: 15px;
}
.search-btn {
  height: 40px;
  padding: 0 16px;
  background: var(--color-primary);
  color: #141414;
  font-size: 15px;
  border-radius: 1px;
}
.user-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.user-item {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 12px 16px;
  cursor: pointer;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.user-name {
  font-size: 16px;
  color: var(--color-text);
}
.role-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 2px;
  background: rgba(249,212,124,0.15);
  color: var(--color-primary);
}
.role-tag.admin {
  background: rgba(249,212,124,0.3);
  color: var(--color-primary);
}
.role-tag.banned {
  background: rgba(255,68,68,0.2);
  color: var(--color-danger);
}
.user-meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--color-text-secondary);
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
