<template>
  <div class="page admin-page">
    <h3 class="section-title">{{ $t('AI 供应商') }}</h3>
    <div class="config-card">
      <div class="config-item">
        <label class="config-label">{{ $t('当前解卦供应商') }}</label>
        <select v-model="configs.LLM_PROVIDER" class="config-input">
          <option v-for="p in providers" :key="p" :value="p">{{ providerLabel(p) }}</option>
        </select>
        <p class="config-hint">{{ $t('切换后立即生效，无需重启服务') }}</p>
      </div>
    </div>

    <h3 class="section-title">{{ $t('额度配置') }}</h3>
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

const PROVIDER_LABELS = {
  deepseek: 'DeepSeek',
  glm: '智谱 GLM',
}

const providers = ref(['deepseek', 'glm'])
const configs = ref({
  LLM_PROVIDER: 'deepseek',
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
    if (Array.isArray(data.configs.LLM_PROVIDERS) && data.configs.LLM_PROVIDERS.length) {
      providers.value = data.configs.LLM_PROVIDERS
    }
    configs.value.LLM_PROVIDER = data.configs.LLM_PROVIDER || 'deepseek'
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

function providerLabel(p) {
  return PROVIDER_LABELS[p] || p
}

async function handleSave() {
  saving.value = true
  saved.value = false
  try {
    await updateAdminConfig(configs.value)
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } catch (e) {
    showToast(e?.response?.data?.error || '保存失败', 'error')
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
select.config-input {
  appearance: none;
  cursor: pointer;
}
.config-hint {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 8px;
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
