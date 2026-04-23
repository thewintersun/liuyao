<template>
  <div class="page reset-page">
    <h2 class="page-title">{{ $t('重置密码') }}</h2>

    <div v-if="checking" class="status-tip">{{ $t('验证中...') }}</div>

    <div v-else-if="invalid" class="status-tip error">
      <p>{{ $t('重置链接无效或已过期') }}</p>
      <p class="back-link" @click="$router.push('/forgot-password')">{{ $t('重新找回密码') }}</p>
    </div>

    <template v-else-if="!done">
      <div class="form-group">
        <input
          v-model="password"
          type="password"
          class="form-input"
          :placeholder="$t('请输入新密码')"
          @keydown.enter="handleSubmit"
        />
      </div>

      <div class="form-group">
        <input
          v-model="confirmPassword"
          type="password"
          class="form-input"
          :placeholder="$t('请确认新密码')"
          @keydown.enter="handleSubmit"
        />
      </div>

      <button class="btn-primary" @click="handleSubmit" :disabled="loading">
        {{ loading ? $t('重置中...') : $t('重置密码') }}
      </button>
    </template>

    <div v-else class="status-tip success">
      <p>{{ $t('密码重置成功') }}</p>
      <p class="back-link" @click="$router.push('/login')">{{ $t('返回登录') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { verifyResetToken, resetPassword } from '../api/index.js'
import { t } from '../utils/locale.js'
import { showToast } from '../utils/toast.js'

const route = useRoute()
const router = useRouter()

const checking = ref(true)
const invalid = ref(false)
const done = ref(false)
const loading = ref(false)
const password = ref('')
const confirmPassword = ref('')

const token = route.query.token || ''

onMounted(async () => {
  if (!token) {
    invalid.value = true
    checking.value = false
    return
  }
  try {
    await verifyResetToken(token)
    checking.value = false
  } catch (e) {
    invalid.value = true
    checking.value = false
  }
})

async function handleSubmit() {
  if (!password.value) {
    showToast(t('请输入新密码'), 'warning')
    return
  }
  if (password.value.length < 6) {
    showToast(t('密码长度不能少于6个字符'), 'warning')
    return
  }
  if (password.value !== confirmPassword.value) {
    showToast(t('两次输入的密码不一致'), 'warning')
    return
  }
  loading.value = true
  try {
    await resetPassword(token, password.value)
    done.value = true
  } catch (e) {
    const msg = e.response?.data?.error || t('重置失败，请稍后重试')
    showToast(msg, 'error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.reset-page {
  max-width: 400px;
  margin: 0 auto;
}
.form-group {
  margin-bottom: 16px;
}
.form-input {
  width: 100%;
  height: 48px;
  background: var(--color-card);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 0 14px;
  font-size: 15px;
  box-sizing: border-box;
}
.form-input::placeholder {
  color: var(--color-text-secondary);
}
.status-tip {
  text-align: center;
  padding: 24px 0;
  color: var(--color-text-secondary);
  font-size: 16px;
}
.status-tip.error {
  color: var(--color-danger);
}
.status-tip.success {
  color: var(--color-primary);
}
.back-link {
  color: var(--color-primary);
  font-size: 14px;
  margin-top: 12px;
  cursor: pointer;
}
</style>
