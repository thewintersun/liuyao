<template>
  <div class="page feedback-page">
    <textarea
      v-model="feedbackText"
      class="feedback-input"
      :placeholder="$t('请输入您的建议或反馈...')"
      rows="8"
    ></textarea>

    <button class="btn-primary" @click="submit" :disabled="loading">
      {{ loading ? $t('提交中...') : $t('提交') }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { submitFeedback } from '../api/index.js'
import { t } from '../utils/locale.js'

const router = useRouter()
const feedbackText = ref('')
const loading = ref(false)

async function submit() {
  if (!feedbackText.value.trim()) {
    alert(t('请输入反馈内容'))
    return
  }

  loading.value = true
  try {
    const result = await submitFeedback(feedbackText.value.trim())
    if (result.status === 'success') {
      alert(t('反馈已提交，感谢您的建议！'))
      router.back()
    } else {
      alert(t('提交失败，请稍后再试'))
    }
  } catch (e) {
    alert(t('提交失败，请稍后再试'))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.feedback-input {
  width: 100%;
  height: 200px;
  background: var(--color-card);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 12px;
  font-size: 15px;
  resize: none;
  margin-bottom: 20px;
}
.feedback-input::placeholder {
  color: var(--color-text-secondary);
}
</style>
