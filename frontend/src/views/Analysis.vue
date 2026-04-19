<template>
  <div class="page analysis-page">
    <p class="instruction-text">
      {{ $t('请输入起卦时所求之事（必填）。以及和所求之事有关的背景，辅助断卦更准确。(比如：事情的背景，当前状态，性别，年龄等，越详细越准确)') }}
    </p>

    <textarea
      v-model="inputText"
      class="input-area"
      :placeholder="$t('请输入所求之事...')"
      rows="6"
    ></textarea>

    <button class="btn-primary" @click="submit" :disabled="loading">{{ $t('解卦') }}</button>

    <p class="disclaimer-text">{{ $t('* 注: 结果AI辅助生成,仅供学习和娱乐') }}</p>

    <!-- 游客次数限制弹窗 -->
    <div class="loading-overlay" v-if="showLimitDialog" @click.self="showLimitDialog = false">
      <div class="limit-dialog">
        <p class="limit-title">{{ $t('免费次数已用完') }}</p>
        <p class="limit-desc">{{ $t('注册账号可获得') + registeredFreeUses + $t('次免费解卦额度') }}</p>
        <button class="btn-primary" @click="goRegister">{{ $t('去注册') }}</button>
        <p class="limit-cancel" @click="showLimitDialog = false">{{ $t('取消') }}</p>
      </div>
    </div>

    <!-- 已登录用户额度用完弹窗 -->
    <div class="loading-overlay" v-if="showNoCreditDialog" @click.self="showNoCreditDialog = false">
      <div class="limit-dialog">
        <p class="limit-title">{{ $t('解卦额度已用完') }}</p>
        <p class="limit-desc">{{ $t('邀请好友即可赠送更多额度') }}</p>
        <button class="btn-primary" @click="goInvite">{{ $t('邀请好友得额度') }}</button>
        <p class="limit-cancel" @click="showNoCreditDialog = false">{{ $t('取消') }}</p>
      </div>
    </div>

    <!-- 加载遮罩 -->
    <div class="loading-overlay" v-if="loading">
      <div class="loading-content">
        <div class="spinner"></div>
        <p class="loading-text">{{ $t('解卦过程大概需要45秒时间，请耐心等待') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { submitHexagram, getQuotaConfig } from '../api/index.js'
import { t } from '../utils/locale.js'

const router = useRouter()
const inputText = ref('')
const loading = ref(false)
const showLimitDialog = ref(false)
const showNoCreditDialog = ref(false)
let guestFreeUses = 1
const registeredFreeUses = ref(50)

onMounted(async () => {
  try {
    const config = await getQuotaConfig()
    guestFreeUses = config.guest_free_uses || 1
    registeredFreeUses.value = config.registered_free_uses || 50
  } catch (e) {}
})

function checkGuestLimit() {
  const token = localStorage.getItem('liuyao_token')
  if (token) return true // 已登录，由后端控制
  const used = parseInt(localStorage.getItem('liuyao_guest_uses') || '0')
  if (used >= guestFreeUses) {
    showLimitDialog.value = true
    return false
  }
  return true
}

function goRegister() {
  showLimitDialog.value = false
  router.push('/login')
}

function goInvite() {
  showNoCreditDialog.value = false
  router.push('/invite')
}

async function submit() {
  if (!inputText.value.trim()) {
    alert(t('请输入起卦时所求之事，这是必填项'))
    return
  }

  const guaXiangInfo = JSON.parse(sessionStorage.getItem('liuyao_guaXiangInfo') || '{}')
  const category = JSON.parse(sessionStorage.getItem('liuyao_category') || '{}')

  if (!guaXiangInfo.maingua_liuqin) {
    alert(t('无法获取卦象数据'))
    return
  }

  if (!checkGuestLimit()) return

  loading.value = true
  try {
    const result = await submitHexagram(guaXiangInfo, inputText.value.trim(), category)
    if (result.status === 'success') {
      // 游客计数 +1
      if (!localStorage.getItem('liuyao_token')) {
        const used = parseInt(localStorage.getItem('liuyao_guest_uses') || '0')
        localStorage.setItem('liuyao_guest_uses', String(used + 1))
      }
      // 更新已登录用户的剩余次数
      if (result.remaining_uses !== undefined) {
        const user = JSON.parse(localStorage.getItem('liuyao_user') || '{}')
        user.free_uses = result.remaining_uses
        localStorage.setItem('liuyao_user', JSON.stringify(user))
      }
      sessionStorage.setItem('liuyao_sessionId', result.session_id)
      sessionStorage.setItem('liuyao_initialMessage', result.message)
      sessionStorage.setItem('liuyao_background', inputText.value.trim())
      router.push('/chat')
    } else {
      alert(t('解卦失败，请重试'))
    }
  } catch (e) {
    if (e.response?.status === 403 && e.response?.data?.error === 'no_credit') {
      showNoCreditDialog.value = true
    } else {
      alert(t('请求失败，请检查网络连接后重试'))
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.instruction-text {
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.8;
  margin-bottom: 16px;
}
.input-area {
  width: 100%;
  height: 150px;
  background: var(--color-card);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 12px;
  font-size: 15px;
  resize: none;
  margin-bottom: 16px;
}
.input-area::placeholder {
  color: var(--color-text-secondary);
}
.disclaimer-text {
  color: var(--color-text-secondary);
  font-size: 12px;
  text-align: center;
  margin-top: 12px;
}
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}
.loading-content {
  text-align: center;
}
.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.loading-text {
  color: var(--color-text);
  font-size: 15px;
}
.limit-dialog {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 28px 24px;
  text-align: center;
  max-width: 300px;
  width: 80%;
}
.limit-title {
  color: var(--color-primary);
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 12px;
}
.limit-desc {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-bottom: 20px;
}
.limit-cancel {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-top: 12px;
  cursor: pointer;
}
</style>
