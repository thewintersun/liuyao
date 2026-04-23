<template>
  <div class="page admin-page">
    <div class="config-card">
      <div class="config-item">
        <label class="config-label">{{ $t('游客免费次数') }}</label>
        <input v-model.number="configs.GUEST_FREE_USES" type="number" class="config-input" min="0" />
      </div>
      <div class="config-item">
        <label class="config-label">{{ $t('注册赠送次数') }}</label>
        <input v-model.number="configs.REGISTERED_FREE_USES" type="number" class="config-input" min="0" />
      </div>
    </div>

    <h3 class="section-title">{{ $t('邀请奖励配置') }}</h3>
    <div class="config-card">
      <div class="config-item">
        <label class="config-label">{{ $t('访问链接奖励（邀请人）') }}</label>
        <input v-model.number="configs.INVITE_VISIT_REWARD" type="number" class="config-input" min="0" />
      </div>
      <div class="config-item">
        <label class="config-label">{{ $t('注册奖励（邀请人）') }}</label>
        <input v-model.number="configs.INVITE_REGISTER_REWARD" type="number" class="config-input" min="0" />
      </div>
      <div class="config-item">
        <label class="config-label">{{ $t('注册奖励（被邀请人）') }}</label>
        <input v-model.number="configs.INVITE_REGISTER_BONUS" type="number" class="config-input" min="0" />
      </div>
      <div class="config-item">
        <label class="config-label">{{ $t('每月邀请上限（人数）') }}</label>
        <input v-model.number="configs.INVITE_MONTHLY_LIMIT" type="number" class="config-input" min="1" />
      </div>
      <div class="config-item">
        <label class="config-label">{{ $t('同IP每日访问上限') }}</label>
        <input v-model.number="configs.INVITE_IP_DAILY_LIMIT" type="number" class="config-input" min="1" />
      </div>
    </div>

    <button class="btn-primary save-btn" @click="handleSave" :disabled="saving">
      {{ saving ? $t('保存中...') : $t('保存') }}
    </button>

    <p class="save-tip" v-if="saved">{{ $t('保存成功') }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAdminConfig, updateAdminConfig } from '../../api/index.js'
import { showToast } from '../../utils/toast.js'

const configs = ref({
  GUEST_FREE_USES: 1,
  REGISTERED_FREE_USES: 50,
  INVITE_VISIT_REWARD: 5,
  INVITE_REGISTER_REWARD: 20,
  INVITE_REGISTER_BONUS: 20,
  INVITE_MONTHLY_LIMIT: 20,
  INVITE_IP_DAILY_LIMIT: 3,
})
const saving = ref(false)
const saved = ref(false)

onMounted(async () => {
  try {
    const data = await getAdminConfig()
    configs.value.GUEST_FREE_USES = parseInt(data.configs.GUEST_FREE_USES) || 1
    configs.value.REGISTERED_FREE_USES = parseInt(data.configs.REGISTERED_FREE_USES) || 50
    configs.value.INVITE_VISIT_REWARD = parseInt(data.configs.INVITE_VISIT_REWARD) || 5
    configs.value.INVITE_REGISTER_REWARD = parseInt(data.configs.INVITE_REGISTER_REWARD) || 20
    configs.value.INVITE_REGISTER_BONUS = parseInt(data.configs.INVITE_REGISTER_BONUS) || 20
    configs.value.INVITE_MONTHLY_LIMIT = parseInt(data.configs.INVITE_MONTHLY_LIMIT) || 20
    configs.value.INVITE_IP_DAILY_LIMIT = parseInt(data.configs.INVITE_IP_DAILY_LIMIT) || 3
  } catch (e) {
    console.error('加载配置失败', e)
  }
})

async function handleSave() {
  saving.value = true
  saved.value = false
  try {
    await updateAdminConfig(configs.value)
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } catch (e) {
    showToast('保存失败', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.section-title {
  color: var(--color-primary);
  font-size: 16px;
  margin-bottom: 12px;
  margin-top: 8px;
}
.config-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 16px;
  margin-bottom: 24px;
}
.config-item {
  margin-bottom: 16px;
}
.config-item:last-child {
  margin-bottom: 0;
}
.config-label {
  display: block;
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-bottom: 8px;
}
.config-input {
  width: 100%;
  height: 44px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 0 12px;
  color: var(--color-text);
  font-size: 16px;
}
.save-btn {
  margin-top: 8px;
}
.save-tip {
  text-align: center;
  color: var(--color-primary);
  font-size: 14px;
  margin-top: 12px;
}
</style>
