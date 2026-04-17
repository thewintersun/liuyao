<template>
  <div class="page account-page">
    <h2 class="page-title">{{ $t('账户') }}</h2>

    <div class="account-card" v-if="user">
      <div class="info-row">
        <span class="info-label">{{ $t('用户名') }}</span>
        <span class="info-value">{{ user.username }}</span>
      </div>
      <div class="info-row email-row">
        <span class="info-label">{{ $t('邮箱') }}</span>
        <span
          v-if="!editingEmail"
          class="info-value email-display"
          @dblclick="startEditEmail"
          @touchstart.passive="onTouchStart"
          @touchend.passive="onTouchEnd"
          @touchcancel.passive="clearLongPress"
        >{{ user.email || $t('未设置') }}<span class="edit-icon" @click="startEditEmail">&#9998;</span></span>
        <div v-else class="email-edit-group">
          <input
            ref="emailInputRef"
            v-model="newEmail"
            type="email"
            class="email-edit-input"
            @keyup.enter="handleChangeEmail"
          />
          <button class="email-save-btn" @click="handleChangeEmail" :disabled="emailLoading">{{ $t('保存') }}</button>
          <button class="email-cancel-btn" @click="editingEmail = false">{{ $t('取消') }}</button>
        </div>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('剩余额度') }}</span>
        <span class="info-value uses-count">{{ user.free_uses }} {{ $t('次') }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('注册时间') }}</span>
        <span class="info-value">{{ user.created_at }}</span>
      </div>
    </div>

    <p class="hint-text">{{ $t('每次AI解卦或追问消耗1次额度，排盘计算不消耗额度') }}</p>

    <div class="section-title" @click="showChangePwd = !showChangePwd">
      {{ $t('修改密码') }}
      <span class="toggle-arrow">{{ showChangePwd ? '▾' : '▸' }}</span>
    </div>
    <div class="change-form" v-if="showChangePwd">
      <input v-model="oldPwd" type="password" class="form-input" :placeholder="$t('原密码')" />
      <input v-model="newPwd" type="password" class="form-input" :placeholder="$t('新密码')" />
      <input v-model="confirmPwd" type="password" class="form-input" :placeholder="$t('确认新密码')" />
      <button class="btn-submit" @click="handleChangePwd" :disabled="pwdLoading">
        {{ pwdLoading ? $t('提交中...') : $t('确认修改') }}
      </button>
    </div>

    <button class="btn-logout" @click="handleLogout">{{ $t('退出登录') }}</button>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getUserInfo, changePassword, changeEmail } from '../api/index.js'
import { t } from '../utils/locale.js'

const router = useRouter()
const user = ref(null)
const editingEmail = ref(false)
const newEmail = ref('')
const emailLoading = ref(false)
const emailInputRef = ref(null)
let longPressTimer = null
const showChangePwd = ref(false)
const oldPwd = ref('')
const newPwd = ref('')
const confirmPwd = ref('')
const pwdLoading = ref(false)

onMounted(async () => {
  const token = localStorage.getItem('liuyao_token')
  if (!token) {
    router.replace('/login')
    return
  }
  try {
    const result = await getUserInfo()
    if (result.status === 'success') {
      user.value = result.user
      localStorage.setItem('liuyao_user', JSON.stringify(result.user))
    }
  } catch (e) {
    if (e.response?.status === 401) {
      localStorage.removeItem('liuyao_token')
      localStorage.removeItem('liuyao_user')
      router.replace('/login')
    }
  }
})

function startEditEmail() {
  newEmail.value = user.value.email || ''
  editingEmail.value = true
  nextTick(() => { emailInputRef.value?.focus() })
}

function onTouchStart() {
  longPressTimer = setTimeout(() => startEditEmail(), 500)
}

function onTouchEnd() { clearLongPress() }

function clearLongPress() {
  if (longPressTimer) { clearTimeout(longPressTimer); longPressTimer = null }
}

async function handleChangeEmail() {
  if (!newEmail.value || !newEmail.value.trim()) { alert(t('邮箱��能为空')); return }
  if (!/^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/.test(newEmail.value.trim())) { alert(t('邮箱格式不正确')); return }
  emailLoading.value = true
  try {
    const result = await changeEmail(newEmail.value.trim())
    user.value = result.user
    localStorage.setItem('liuyao_user', JSON.stringify(result.user))
    editingEmail.value = false
    alert(t('邮箱修改成功'))
  } catch (e) {
    alert(e.response?.data?.error || t('修改失败'))
  } finally {
    emailLoading.value = false
  }
}

async function handleChangePwd() {
  if (!oldPwd.value) { alert(t('请输入原密码')); return }
  if (!newPwd.value || newPwd.value.length < 6) { alert(t('新密码长度不能少于6个字符')); return }
  if (newPwd.value !== confirmPwd.value) { alert(t('两次输入的密码不一致')); return }
  pwdLoading.value = true
  try {
    await changePassword(oldPwd.value, newPwd.value)
    alert(t('密码修改成功'))
    oldPwd.value = ''
    newPwd.value = ''
    confirmPwd.value = ''
    showChangePwd.value = false
  } catch (e) {
    alert(e.response?.data?.error || t('修改失败'))
  } finally {
    pwdLoading.value = false
  }
}

function handleLogout() {
  localStorage.removeItem('liuyao_token')
  localStorage.removeItem('liuyao_user')
  router.replace('/settings')
}
</script>

<style scoped>
.account-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 16px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(249, 212, 124, 0.15);
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
.email-row .info-label {
  flex-shrink: 0;
}
.email-display {
  user-select: none;
  -webkit-user-select: none;
  cursor: default;
  display: flex;
  align-items: center;
  gap: 6px;
}
.edit-icon {
  color: var(--color-text-secondary);
  font-size: 14px;
  cursor: pointer;
  flex-shrink: 0;
}
.email-edit-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
  margin-left: 12px;
}
.email-edit-input {
  flex: 1;
  min-width: 0;
  height: 34px;
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-primary);
  border-radius: 4px;
  padding: 0 10px;
  font-size: 14px;
  box-sizing: border-box;
}
.email-save-btn {
  flex-shrink: 0;
  height: 34px;
  padding: 0 12px;
  background: var(--color-primary);
  color: #141414;
  font-size: 14px;
  border-radius: 4px;
}
.email-save-btn:disabled {
  opacity: 0.5;
}
.email-cancel-btn {
  flex-shrink: 0;
  height: 34px;
  padding: 0 10px;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 14px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
}
.uses-count {
  color: var(--color-primary);
  font-weight: bold;
  font-size: 18px;
}
.hint-text {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 13px;
  margin-bottom: 24px;
}
.section-title {
  color: var(--color-text);
  font-size: 15px;
  padding: 12px 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.toggle-arrow {
  font-size: 12px;
  color: var(--color-text-secondary);
}
.change-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}
.form-input {
  width: 100%;
  height: 44px;
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
.btn-submit {
  width: 100%;
  height: 44px;
  background: var(--color-primary);
  color: #141414;
  font-size: 15px;
  border-radius: 4px;
}
.btn-submit:disabled {
  opacity: 0.5;
}
.btn-logout {
  width: 100%;
  height: 44px;
  background: transparent;
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
  border-radius: 4px;
  font-size: 15px;
  cursor: pointer;
}
</style>
