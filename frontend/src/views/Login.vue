<template>
  <div class="page login-page">
    <h2 class="page-title">{{ $t(isLogin ? '登录' : '注册') }}</h2>

    <div class="form-group">
      <input
        v-model="username"
        type="text"
        class="form-input"
        :placeholder="$t('请输入用户名')"
        maxlength="20"
        @keydown.enter="handleSubmit"
      />
    </div>

    <div class="form-group">
      <input
        v-model="password"
        type="password"
        class="form-input"
        :placeholder="$t('请输入密码')"
        @keydown.enter="handleSubmit"
      />
    </div>

    <div class="forgot-link" v-if="isLogin">
      <span @click="$router.push('/forgot-password')">{{ $t('忘记密码？') }}</span>
    </div>

    <div class="form-group" v-if="!isLogin">
      <input
        v-model="inviteCode"
        type="text"
        class="form-input"
        :placeholder="$t('邀请码（选填）')"
        maxlength="6"
        @keydown.enter="handleSubmit"
      />
    </div>

    <div class="form-group captcha-row" v-if="!isLogin">
      <img
        v-if="captchaImage"
        :src="captchaImage"
        class="captcha-img"
        @click="refreshCaptcha"
        :title="$t('点击刷新验证码')"
      />
      <input
        v-model="captchaText"
        type="text"
        class="form-input captcha-input"
        :placeholder="$t('验证码')"
        maxlength="4"
        @keydown.enter="handleSubmit"
      />
      <button type="button" class="captcha-refresh" @click="refreshCaptcha" :title="$t('刷新验证码')">&#x21bb;</button>
    </div>

    <div class="form-group agree-row" v-if="!isLogin">
      <label class="agree-label">
        <input type="checkbox" v-model="agreedTerms" class="agree-checkbox" />
        <span>{{ $t('我已阅读并同意') }}
          <span class="agree-link" @click.prevent="openTerms">{{ $t('《用户协议与隐私政策》') }}</span>
        </span>
      </label>
    </div>

    <!-- 二次确认弹窗 -->
    <div class="terms-overlay" v-if="showTermsDialog" @click.self="showTermsDialog = false">
      <div class="terms-dialog">
        <p class="terms-dialog-title">{{ $t('温馨提示') }}</p>
        <p class="terms-dialog-body">
          {{ $t('请先阅读并同意') }}
          <span class="agree-link" @click="openTerms">{{ $t('《用户协议与隐私政策》') }}</span>
          {{ $t('后再注册。') }}
        </p>
        <div class="terms-dialog-btns">
          <button class="btn-cancel" @click="showTermsDialog = false">{{ $t('取消') }}</button>
          <button class="btn-primary btn-agree" @click="agreeAndSubmit">{{ $t('同意并注册') }}</button>
        </div>
      </div>
    </div>

    <button class="btn-primary" @click="handleSubmit" :disabled="loading">
      {{ loading ? $t('请稍候...') : $t(isLogin ? '登录' : '注册') }}
    </button>

    <p class="switch-text" @click="toggleMode">
      {{ $t(isLogin ? '没有账号？点此注册' : '已有账号？点此登录') }}
    </p>

    <p class="hint-text" v-if="!isLogin">
      {{ $t('注册后可获得') }}{{ registeredUses }}{{ $t('次免费解卦额度') }}
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { login, register, getCaptcha, getQuotaConfig } from '../api/index.js'
import { t } from '../utils/locale.js'

const router = useRouter()
const isLogin = ref(true)
const username = ref('')
const password = ref('')
const captchaId = ref('')
const captchaText = ref('')
const captchaImage = ref('')
const inviteCode = ref('')
const loading = ref(false)
const agreedTerms = ref(false)
const showTermsDialog = ref(false)
const registeredUses = ref(3)



onMounted(async () => {
  // 已登录则跳转到账户页
  if (localStorage.getItem('liuyao_token')) {
    router.replace('/account')
    return
  }
  // 从 sessionStorage 自动填入邀请码
  const refCode = sessionStorage.getItem('liuyao_ref_code')
  if (refCode) {
    inviteCode.value = refCode
  }
  try {
    const res = await getQuotaConfig()
    // registeredUses 不从 quota 接口获取，保持默认
  } catch (e) {}
})

async function refreshCaptcha() {
  try {
    const res = await getCaptcha()
    captchaId.value = res.captcha_id
    captchaImage.value = res.image
    captchaText.value = ''
  } catch (e) {
    console.error('获取验证码失败', e)
  }
}

function toggleMode() {
  isLogin.value = !isLogin.value
  captchaText.value = ''
  agreedTerms.value = false
  showTermsDialog.value = false
  if (!isLogin.value) {
    refreshCaptcha()
  }
}

function openTerms() {
  window.open(location.origin + '/terms-privacy', '_blank')
}

function agreeAndSubmit() {
  agreedTerms.value = true
  showTermsDialog.value = false
  handleSubmit()
}

async function handleSubmit() {
  if (!username.value.trim()) {
    alert(t('请输入用户名'))
    return
  }
  if (!password.value) {
    alert(t('请输入密码'))
    return
  }
  if (!isLogin.value) {
    if (password.value.length < 6) {
      alert(t('密码长度不能少于6个字符'))
      return
    }
    if (!captchaText.value.trim()) {
      alert(t('请输入验证码'))
      return
    }
  }

  if (!isLogin.value && !agreedTerms.value) {
    showTermsDialog.value = true
    return
  }

  loading.value = true
  try {
    const result = isLogin.value
      ? await login(username.value.trim(), password.value)
      : await register(username.value.trim(), password.value, '', captchaId.value, captchaText.value.trim(), agreedTerms.value, inviteCode.value.trim())
    if (result.status === 'success') {
      localStorage.setItem('liuyao_token', result.token)
      localStorage.setItem('liuyao_user', JSON.stringify(result.user))
      // 登录成功后清除游客计数
      localStorage.removeItem('liuyao_guest_uses')
      // 注册成功后清除邀请码
      sessionStorage.removeItem('liuyao_ref_code')
      router.replace('/account')
    } else {
      alert(result.error || t('操作失败'))
    }
  } catch (e) {
    const msg = e.response?.data?.error || t('网络错误，请稍后重试')
    alert(msg)
    if (!isLogin.value) refreshCaptcha()
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
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
.switch-text {
  text-align: center;
  color: var(--color-primary);
  font-size: 14px;
  margin-top: 16px;
  cursor: pointer;
}
.hint-text {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 13px;
  margin-top: 12px;
}
.captcha-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.captcha-img {
  height: 48px;
  border-radius: 4px;
  cursor: pointer;
  flex-shrink: 0;
}
.captcha-input {
  flex: 1;
  min-width: 0;
}
.captcha-refresh {
  width: 40px;
  height: 48px;
  background: var(--color-card);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 20px;
  cursor: pointer;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.captcha-refresh:hover {
  background: var(--color-border);
}
.forgot-link {
  text-align: right;
  margin-bottom: 16px;
  margin-top: -8px;
}
.forgot-link span {
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
}
.forgot-link span:hover {
  color: var(--color-primary);
}
.agree-row {
  margin-bottom: 12px;
}
.agree-label {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.5;
}
.agree-checkbox {
  margin-top: 2px;
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
  flex-shrink: 0;
  cursor: pointer;
}
.agree-link {
  color: var(--color-primary);
  text-decoration: underline;
  cursor: pointer;
}
.terms-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.terms-dialog {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 24px;
  max-width: 320px;
  width: 88%;
}
.terms-dialog-title {
  color: var(--color-primary);
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 12px;
  text-align: center;
}
.terms-dialog-body {
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.7;
  margin-bottom: 20px;
  text-align: center;
}
.terms-dialog-btns {
  display: flex;
  gap: 12px;
}
.btn-cancel {
  flex: 1;
  height: 44px;
  background: transparent;
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 15px;
  cursor: pointer;
}
.btn-agree {
  flex: 1;
  height: 44px;
  font-size: 15px;
}
</style>
