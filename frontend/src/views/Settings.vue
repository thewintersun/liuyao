<template>
  <div class="page settings-page">
    <h2 class="page-title">{{ $t('设置') }}</h2>
    <div class="menu-list">
      <div class="menu-item" @click="goAccount">
        <span class="menu-title">{{ $t(isLoggedIn ? '账户' : '登录 / 注册') }}</span>
        <span class="menu-extra" v-if="isLoggedIn">{{ username }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/guide')">
        <span class="menu-title">{{ $t('起卦必读') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/disclaimer')">
        <span class="menu-title">{{ $t('免责声明') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/terms-privacy')">
        <span class="menu-title">{{ $t('用户协议与隐私政策') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="$router.push('/feedback')">
        <span class="menu-title">{{ $t('建议反馈') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" v-if="isLoggedIn" @click="$router.push('/invite')">
        <span class="menu-title">{{ $t('邀请好友得额度') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" @click="showLangPicker = true">
        <span class="menu-title">{{ $t('语言') }} / Language</span>
        <span class="menu-extra">{{ currentLangLabel }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
      <div class="menu-item" v-if="isAdmin" @click="$router.push('/admin')">
        <span class="menu-title">{{ $t('后台管理') }}</span>
        <span class="menu-arrow">&#8250;</span>
      </div>
    </div>

    <div class="menu-list" v-if="isLoggedIn" style="margin-top: 24px;">
      <div class="menu-item logout-item" @click="handleLogout">
        <span class="menu-title logout-text">{{ $t('退出登录') }}</span>
      </div>
    </div>

    <!-- 语言选择弹窗 -->
    <div class="lang-overlay" v-if="showLangPicker" @click.self="showLangPicker = false">
      <div class="lang-dialog">
        <p class="lang-dialog-title">{{ $t('选择语言') }}</p>
        <div
          v-for="opt in langOptions"
          :key="opt.value"
          class="lang-option"
          :class="{ active: currentLangSetting === opt.value }"
          @click="selectLang(opt.value)"
        >
          {{ opt.label }}
        </div>
        <p class="lang-cancel" @click="showLangPicker = false">{{ $t('取消') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { t, getLang, setLang } from '../utils/locale.js'

const router = useRouter()
const isLoggedIn = ref(false)
const username = ref('')
const isAdmin = ref(false)
const showLangPicker = ref(false)

const currentLangSetting = ref(localStorage.getItem('liuyao_lang') || 'auto')

const langOptions = [
  { value: 'auto', label: t('跟随系统') + ' / Auto' },
  { value: 'zh-CN', label: '简体中文' },
  { value: 'zh-TW', label: '繁體中文' },
]

const currentLangLabel = computed(() => {
  const opt = langOptions.find(o => o.value === currentLangSetting.value)
  return opt ? opt.label : langOptions[0].label
})

function selectLang(lang) {
  setLang(lang)
  showLangPicker.value = false
  location.reload()
}

function checkLoginState() {
  const token = localStorage.getItem('liuyao_token')
  const user = JSON.parse(localStorage.getItem('liuyao_user') || '{}')
  isLoggedIn.value = !!token
  username.value = user.username || ''
  isAdmin.value = user.role === 'admin'
}

onMounted(checkLoginState)

function goAccount() {
  if (isLoggedIn.value) {
    router.push('/account')
  } else {
    router.push('/login')
  }
}

function handleLogout() {
  localStorage.removeItem('liuyao_token')
  localStorage.removeItem('liuyao_user')
  isLoggedIn.value = false
  username.value = ''
}
</script>

<style scoped>
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
.menu-extra {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-right: 8px;
}
.menu-arrow {
  color: var(--color-text-secondary);
  font-size: 20px;
}
.logout-item {
  justify-content: center;
}
.logout-text {
  color: var(--color-danger);
  text-align: center;
  flex: none;
}
.lang-overlay {
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
.lang-dialog {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  max-width: 300px;
  width: 80%;
}
.lang-dialog-title {
  color: var(--color-primary);
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 16px;
}
.lang-option {
  padding: 14px 0;
  color: var(--color-text);
  font-size: 16px;
  cursor: pointer;
  border-bottom: 1px solid rgba(249,212,124,0.15);
}
.lang-option:last-of-type {
  border-bottom: none;
}
.lang-option.active {
  color: var(--color-primary);
  font-weight: bold;
}
.lang-cancel {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-top: 16px;
  cursor: pointer;
}
</style>
