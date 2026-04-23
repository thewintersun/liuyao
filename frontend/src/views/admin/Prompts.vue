<template>
  <div class="page admin-page">
    <div class="prompt-section">
      <label class="prompt-label">{{ $t('系统提示词') }}</label>
      <textarea v-model="prompts.SYSTEM_PROMPT" class="prompt-textarea" rows="6"></textarea>
    </div>

    <div class="prompt-section">
      <label class="prompt-label">{{ $t('六爻分析提示词') }}</label>
      <p class="prompt-hint">{{ $t('请保留 {liuyao_data} 占位符') }}</p>
      <textarea v-model="prompts.LIUYAO_PROMPT" class="prompt-textarea" rows="12"></textarea>
    </div>

    <button class="btn-primary save-btn" @click="handleSave" :disabled="saving">
      {{ saving ? $t('保存中...') : $t('保存') }}
    </button>

    <p class="save-tip" v-if="saved">{{ $t('保存成功') }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAdminPrompts, updateAdminPrompts } from '../../api/index.js'
import { showToast } from '../../utils/toast.js'

const prompts = ref({
  SYSTEM_PROMPT: '',
  LIUYAO_PROMPT: '',
})
const saving = ref(false)
const saved = ref(false)

onMounted(async () => {
  try {
    const data = await getAdminPrompts()
    prompts.value = data.prompts
  } catch (e) {
    console.error('加载提示词失败', e)
  }
})

async function handleSave() {
  if (!prompts.value.LIUYAO_PROMPT.includes('{liuyao_data}')) {
    showToast('六爻分析提示词必须包含 {liuyao_data} 占位符', 'warning')
    return
  }
  saving.value = true
  saved.value = false
  try {
    await updateAdminPrompts(prompts.value)
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
.prompt-section {
  margin-bottom: 20px;
}
.prompt-label {
  display: block;
  color: var(--color-primary);
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 8px;
}
.prompt-hint {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin-bottom: 8px;
}
.prompt-textarea {
  width: 100%;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 12px;
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
}
.save-btn {
  margin-top: 4px;
}
.save-tip {
  text-align: center;
  color: var(--color-primary);
  font-size: 14px;
  margin-top: 12px;
}
</style>
