<template>
  <div class="page admin-page">
    <div class="session-info" v-if="detail">
      <div class="info-row" v-if="detail.title">
        <span class="info-label">{{ $t('标题') }}</span>
        <span class="info-value">{{ detail.title }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('会话ID') }}</span>
        <span class="info-value mono">{{ sessionId }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{{ $t('数据来源') }}</span>
        <span class="info-value">{{ sourceLabel }}</span>
      </div>
      <div class="info-row" v-if="detail.date">
        <span class="info-label">{{ $t('日期') }}</span>
        <span class="info-value">{{ detail.date }}</span>
      </div>
      <div class="info-row" v-if="detail.logs && detail.logs.length">
        <span class="info-label">{{ $t('操作记录') }}</span>
        <span class="info-value">{{ detail.logs.length }} {{ $t('条') }}</span>
      </div>
    </div>

    <div class="log-entries" v-if="detail && detail.logs && detail.logs.length">
      <div class="section-title">{{ $t('操作日志') }}</div>
      <div class="log-entry" v-for="log in detail.logs" :key="log.id">
        <span class="log-action-tag">{{ log.action }}</span>
        <span class="log-username">{{ log.username || (log.user_id ? ('ID:' + log.user_id) : $t('游客')) }}</span>
        <span class="log-time">{{ log.created_at }}</span>
      </div>
    </div>

    <div class="chat-section" v-if="detail && detail.messages && detail.messages.length">
      <div class="section-title">{{ $t('聊天记录') }}</div>
      <div class="chat-list">
        <div
          class="chat-bubble"
          :class="msg.role"
          v-for="(msg, idx) in detail.messages"
          :key="idx"
        >
          <div class="bubble-role">{{ msg.role === 'user' ? $t('用户') : 'AI' }}</div>
          <div class="bubble-content" v-if="msg.role === 'assistant'" v-html="renderMarkdown(msg.content)"></div>
          <div class="bubble-content" v-else>{{ msg.content }}</div>
        </div>
      </div>
    </div>

    <div class="empty-tip" v-if="detail && (!detail.messages || !detail.messages.length)">
      {{ $t('无聊天记录') }}
    </div>

    <div class="empty-tip" v-if="!detail && !loading">{{ $t('未找到该会话记录') }}</div>
    <div class="empty-tip" v-if="loading">{{ $t('加载中...') }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { getSessionDetail } from '../../api/index.js'

const route = useRoute()
const sessionId = route.params.sessionId
const detail = ref(null)
const loading = ref(true)

const sourceLabel = computed(() => {
  if (!detail.value) return ''
  const map = { record: '已保存记录', memory: '活跃会话（内存）', logs_only: '仅日志' }
  return map[detail.value.source] || detail.value.source
})

function renderMarkdown(text) {
  return DOMPurify.sanitize(marked(text))
}

onMounted(async () => {
  try {
    const data = await getSessionDetail(sessionId)
    detail.value = data
  } catch (e) {
    console.error('加载会话详情失败', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.session-info {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 12px 14px;
  margin-bottom: 16px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(249,212,124,0.1);
}
.info-row:last-child {
  border-bottom: none;
}
.info-label {
  color: var(--color-text-secondary);
  font-size: 14px;
}
.info-value {
  color: var(--color-text);
  font-size: 14px;
}
.info-value.mono {
  font-family: monospace;
}
.section-title {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin-bottom: 8px;
  padding-left: 2px;
}
.log-entries {
  margin-bottom: 16px;
}
.log-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  margin-bottom: 4px;
  font-size: 13px;
}
.log-action-tag {
  padding: 1px 6px;
  background: rgba(249,212,124,0.15);
  color: var(--color-primary);
  border-radius: 2px;
  font-size: 12px;
}
.log-username {
  color: var(--color-text);
  flex: 1;
}
.log-time {
  color: var(--color-text-secondary);
  font-size: 12px;
}
.chat-section {
  margin-bottom: 16px;
}
.chat-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chat-bubble {
  padding: 10px 14px;
  border-radius: 4px;
  max-width: 90%;
}
.chat-bubble.user {
  background: rgba(249,212,124,0.12);
  border: 1px solid rgba(249,212,124,0.25);
  align-self: flex-end;
}
.chat-bubble.assistant {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  align-self: flex-start;
}
.bubble-role {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}
.bubble-content {
  font-size: 14px;
  color: var(--color-text);
  word-break: break-word;
  line-height: 1.6;
}
.chat-bubble.user .bubble-content {
  white-space: pre-wrap;
}
.chat-bubble.assistant .bubble-content :deep(h1),
.chat-bubble.assistant .bubble-content :deep(h2),
.chat-bubble.assistant .bubble-content :deep(h3) {
  margin: 8px 0 4px;
  font-size: 16px;
}
.chat-bubble.assistant .bubble-content :deep(p) {
  margin: 4px 0;
}
.chat-bubble.assistant .bubble-content :deep(ul),
.chat-bubble.assistant .bubble-content :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.chat-bubble.assistant .bubble-content :deep(code) {
  background: rgba(249,212,124,0.1);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 13px;
}
.empty-tip {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 40px 0;
}
</style>
