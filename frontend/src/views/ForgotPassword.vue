<template>
  <div class="page forgot-page">
    <h2 class="page-title">{{ $t('找回密码') }}</h2>

    <template v-if="!sent">
      <div class="form-group">
        <input
          v-model="email"
          type="email"
          class="form-input"
          :placeholder="$t('请输入注册邮箱')"
          @keydown.enter="handleSubmit"
        />
      </div>

      <button class="btn-primary" @click="handleSubmit" :disabled="loading">
        {{ loading ? $t('发送中...') : $t('发送重置邮件') }}
      </button>
    </template>

    <div class="success-tip" v-else>
      <p>{{ $t('重置邮件已发送，请查收邮箱') }}</p>
      <p class="sub-tip">{{ $t('如未收到，请检查垃圾邮件') }}</p>
    </div>

    <p class="back-link" @click="$router.push('/login')">{{ $t('返回登录') }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { forgotPassword } from '../api/index.js'
import { t } from '../utils/locale.js'

const email = ref('')
const loading = ref(false)
const sent = ref(false)

async function handleSubmit() {
  if (!email.value.trim()) {
    alert(t('请输入邮箱'))
    return
  }
  loading.value = true
  try {
    await forgotPassword(email.value.trim())
    sent.value = true
  } catch (e) {
    const msg = e.response?.data?.error || t('网络错误，请稍后重试')
    alert(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.forgot-page {
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
.success-tip {
  text-align: center;
  padding: 24px 0;
  color: var(--color-primary);
  font-size: 16px;
}
.sub-tip {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin-top: 8px;
}
.back-link {
  text-align: center;
  color: var(--color-primary);
  font-size: 14px;
  margin-top: 16px;
  cursor: pointer;
}
</style>
