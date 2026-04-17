<template>
  <div class="page admin-page">
    <div class="user-card" v-if="user">
      <div class="info-row">
        <span class="info-label">{{ $t('用户名') }}</span>
        <span class="info-value">{{ user.username }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('角色') }}</span>
        <span class="role-tag" :class="user.role">{{ roleLabel(user.role) }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('邮箱') }}</span>
        <span class="info-value">{{ user.email || '-' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('剩余额度') }}</span>
        <span class="info-value">{{ user.free_uses }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('注册时间') }}</span>
        <span class="info-value">{{ user.created_at }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('最后登录时间') }}</span>
        <span class="info-value">{{ user.last_login_at || '-' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('最后登录 IP') }}</span>
        <span class="info-value">{{ user.last_login_ip || '-' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('登录地理位置') }}</span>
        <span class="info-value">{{ user.last_login_location || '-' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('总使用次数') }}</span>
        <span class="info-value">{{ user.total_uses }}</span>
      </div>
      <div class="info-row" v-for="(cnt, action) in user.action_stats" :key="action">
        <span class="info-label">{{ action }}</span>
        <span class="info-value">{{ cnt }} {{ $t('次') }}</span>
      </div>
    </div>

    <div class="action-section" v-if="user">
      <div class="quota-adjust">
        <span class="action-label">{{ $t('调整额度') }}</span>
        <input v-model.number="newQuota" type="number" class="quota-input" min="0" />
        <button class="action-btn" @click="handleQuota">{{ $t('确认') }}</button>
      </div>

      <div class="quota-adjust">
        <span class="action-label">{{ $t('重置密码') }}</span>
        <input v-model="newPassword" type="text" class="quota-input" :placeholder="$t('输入新密码')" />
        <button class="action-btn" @click="handleResetPassword">{{ $t('确认') }}</button>
      </div>

      <button
        v-if="user.role !== 'admin'"
        class="action-btn-full"
        :class="user.role === 'banned' ? 'unban' : 'ban'"
        @click="handleBanToggle"
      >
        {{ user.role === 'banned' ? $t('解封用户') : $t('封禁用户') }}
      </button>
    </div>

    <div class="empty-tip" v-if="!user && !loading">{{ $t('用户不存在') }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getAdminUserDetail, updateUserQuota, banUser, unbanUser, adminResetPassword } from '../../api/index.js'

const route = useRoute()
const user = ref(null)
const newQuota = ref(0)
const newPassword = ref('')
const loading = ref(true)

function roleLabel(role) {
  const map = { admin: '管理员', banned: '已封禁', user: '普通用户' }
  return map[role] || role
}

async function loadUser() {
  loading.value = true
  try {
    const data = await getAdminUserDetail(route.params.id)
    user.value = data.user
    newQuota.value = data.user.free_uses
  } catch (e) {
    console.error('加载用户详情失败', e)
  } finally {
    loading.value = false
  }
}

async function handleQuota() {
  try {
    await updateUserQuota(user.value.id, newQuota.value)
    user.value.free_uses = newQuota.value
  } catch (e) {
    alert('调整额度失败')
  }
}

async function handleResetPassword() {
  if (!newPassword.value || newPassword.value.length < 6) {
    alert('密码长度不能少于6个字符')
    return
  }
  try {
    await adminResetPassword(user.value.id, newPassword.value)
    alert('密码已重置')
    newPassword.value = ''
  } catch (e) {
    alert(e.response?.data?.error || '重置失败')
  }
}

async function handleBanToggle() {
  try {
    if (user.value.role === 'banned') {
      await unbanUser(user.value.id)
      user.value.role = 'user'
    } else {
      await banUser(user.value.id)
      user.value.role = 'banned'
    }
  } catch (e) {
    alert(e.response?.data?.error || '操作失败')
  }
}

onMounted(loadUser)
</script>

<style scoped>
.user-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 16px;
  margin-bottom: 20px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(249,212,124,0.1);
}
.info-row:last-child {
  border-bottom: none;
}
.info-label {
  color: var(--color-text-secondary);
  font-size: 15px;
}
.info-value {
  color: var(--color-text);
  font-size: 15px;
}
.role-tag {
  font-size: 13px;
  padding: 2px 10px;
  border-radius: 2px;
  background: rgba(249,212,124,0.15);
  color: var(--color-primary);
}
.role-tag.admin {
  background: rgba(249,212,124,0.3);
}
.role-tag.banned {
  background: rgba(255,68,68,0.2);
  color: var(--color-danger);
}
.action-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.quota-adjust {
  display: flex;
  align-items: center;
  gap: 8px;
}
.action-label {
  color: var(--color-text);
  font-size: 15px;
  white-space: nowrap;
}
.quota-input {
  flex: 1;
  height: 40px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 0 12px;
  color: var(--color-text);
  font-size: 15px;
}
.action-btn {
  height: 40px;
  padding: 0 20px;
  background: var(--color-primary);
  color: #141414;
  font-size: 15px;
  border-radius: 1px;
}
.action-btn-full {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 1px;
}
.action-btn-full.ban {
  background: var(--color-danger);
  color: #fff;
}
.action-btn-full.unban {
  background: var(--color-primary);
  color: #141414;
}
.empty-tip {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 40px 0;
}
</style>
