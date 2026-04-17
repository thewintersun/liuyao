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

    <button class="btn-primary save-btn" @click="handleSave" :disabled="saving">
      {{ saving ? $t('保存中...') : $t('保存') }}
    </button>

    <p class="save-tip" v-if="saved">{{ $t('保存成功') }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAdminConfig, updateAdminConfig } from '../../api/index.js'

const configs = ref({
  GUEST_FREE_USES: 1,
  REGISTERED_FREE_USES: 50,
})
const saving = ref(false)
const saved = ref(false)

onMounted(async () => {
  try {
    const data = await getAdminConfig()
    configs.value.GUEST_FREE_USES = parseInt(data.configs.GUEST_FREE_USES) || 1
    configs.value.REGISTERED_FREE_USES = parseInt(data.configs.REGISTERED_FREE_USES) || 50
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
    alert('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
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
