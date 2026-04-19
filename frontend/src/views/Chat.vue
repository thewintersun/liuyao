<template>
  <div class="chat-page">
    <div class="chat-tip">{{ $t('您可以继续针对结果继续追问') }}</div>

    <div class="chat-messages" ref="messagesRef">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message"
        :class="msg.role"
      >
        <div class="bubble" v-if="msg.role === 'assistant'" v-html="renderMarkdown(msg.content)"></div>
        <div class="bubble" v-else>{{ msg.content }}</div>
      </div>
      <div v-if="loading" class="message assistant">
        <div class="bubble loading-bubble">
          <span class="dot-loading">{{ $t('思考中...') }}</span>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <textarea
        v-model="inputText"
        class="chat-input"
        :placeholder="$t('输入追问内容...')"
        rows="1"
        @keydown.enter.exact.prevent="send"
      ></textarea>
      <button class="send-btn" @click="send" :disabled="loading || !inputText.trim()">{{ $t('发送') }}</button>
    </div>

    <!-- 次数限制弹窗 -->
    <div class="limit-overlay" v-if="showLimitDialog" @click.self="showLimitDialog = false">
      <div class="limit-dialog">
        <p class="limit-title">{{ $t('免费次数已用完') }}</p>
        <p class="limit-desc">{{ $t('注册账号可获得更多免费解卦额度') }}</p>
        <button class="btn-primary" @click="goRegister">{{ $t('去注册') }}</button>
        <p class="limit-cancel" @click="showLimitDialog = false">{{ $t('取消') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { chatMessage, restoreChat, getQuotaConfig } from '../api/index.js'
import { getRecordById, updateRecord, saveRecord } from '../store/records.js'
import { t } from '../utils/locale.js'

const router = useRouter()
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const messagesRef = ref(null)
const showLimitDialog = ref(false)
let guestFreeUses = 1

let sessionId = ''
let currentRecordId = ''

async function persistMessages() {
  if (currentRecordId) {
    await updateRecord(currentRecordId, { messages: messages.value, sessionId })
  }
}

onMounted(async () => {
  const restoreRecordId = sessionStorage.getItem('liuyao_restoreRecordId')

  if (restoreRecordId) {
    // 入口B：从 Records 恢复对话
    sessionStorage.removeItem('liuyao_restoreRecordId')
    const record = await getRecordById(restoreRecordId)
    if (!record || !record.messages) {
      router.push('/')
      return
    }
    currentRecordId = record.id
    messages.value = [...record.messages]
    // 恢复后端会话
    try {
      const res = await restoreChat(record.sessionId || '', record.messages)
      sessionId = res.session_id
      await persistMessages()
    } catch (e) {
      // 恢复失败仍显示历史，但追问可能失败
      sessionId = record.sessionId || ''
    }
  } else {
    // 入口A：从 Analysis 进入（新对话）
    sessionId = sessionStorage.getItem('liuyao_sessionId') || ''
    const initialMessage = sessionStorage.getItem('liuyao_initialMessage') || ''

    if (!sessionId || !initialMessage) {
      router.push('/')
      return
    }

    messages.value.push({ role: 'assistant', content: initialMessage })

    // 关联或创建记录
    const savedRecordId = sessionStorage.getItem('liuyao_currentRecordId')
    const category = JSON.parse(sessionStorage.getItem('liuyao_category') || '{}')
    const background = sessionStorage.getItem('liuyao_background') || ''
    const guaXiangInfo = JSON.parse(sessionStorage.getItem('liuyao_guaXiangInfo') || '{}')

    try {
      if (savedRecordId) {
        currentRecordId = savedRecordId
        await updateRecord(currentRecordId, {
          sessionId,
          messages: messages.value,
          category,
          background,
          guaXiangInfo
        })
      } else {
        // 自动创建记录，标题优先取"所求之事"，fallback 到起卦时间
        const dateStr = sessionStorage.getItem('liuyao_date')
        const dateInfo = dateStr ? JSON.parse(dateStr) : null
        const dateTitle = dateInfo
          ? `${dateInfo.year}年${dateInfo.month}月${dateInfo.day}日 ${dateInfo.hour}时`
          : ''
        const guaTitle = (background && background.trim().slice(0, 30))
          || dateTitle
          || guaXiangInfo.bengua_name
          || t('未命名卦例')
        const date = dateInfo
          ? new Date(dateInfo.year, dateInfo.month - 1, dateInfo.day, dateInfo.hour)
          : new Date()
        const yaoStr = sessionStorage.getItem('liuyao_yaoValues')
        const yaoValues = yaoStr ? JSON.parse(yaoStr) : []
        const record = await saveRecord(guaTitle, date, yaoValues)
        currentRecordId = record.id
        await updateRecord(currentRecordId, {
          sessionId,
          messages: messages.value,
          category,
          background,
          guaXiangInfo
        })
      }
    } catch (e) {
      console.error('记录持久化失败:', e)
    }

    // 清除临时数据
    sessionStorage.removeItem('liuyao_sessionId')
    sessionStorage.removeItem('liuyao_initialMessage')
    sessionStorage.removeItem('liuyao_background')
    sessionStorage.removeItem('liuyao_currentRecordId')
  }

  try {
    const config = await getQuotaConfig()
    guestFreeUses = config.guest_free_uses || 1
  } catch (e) {}
})

function renderMarkdown(text) {
  return DOMPurify.sanitize(marked(text))
}

function checkGuestLimit() {
  const token = localStorage.getItem('liuyao_token')
  if (token) return true
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

async function send() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  if (!checkGuestLimit()) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const result = await chatMessage(sessionId, text)
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
      messages.value.push({ role: 'assistant', content: result.message })
    } else {
      messages.value.push({ role: 'assistant', content: t('抱歉，获取回复失败，请重试。') })
    }
  } catch (e) {
    if (e.response?.status === 403 && e.response?.data?.error === 'no_credit') {
      messages.value.push({ role: 'assistant', content: t('额度已用完，无法继续追问。') })
    } else {
      messages.value.push({ role: 'assistant', content: t('网络错误，请检查连接后重试。') })
    }
  } finally {
    loading.value = false
    await persistMessages()
    await scrollToBottom()
  }
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 44px - 60px);
}
.chat-tip {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 13px;
  padding: 8px;
  background: var(--color-card);
  border-bottom: 1px solid var(--color-border);
}
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}
.message {
  margin-bottom: 12px;
  display: flex;
}
.message.assistant {
  justify-content: flex-start;
}
.message.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
}
.message.assistant .bubble {
  background: #FFFFFF;
  color: #333333;
}
.message.user .bubble {
  background: var(--color-user-bubble);
  color: #FFFFFF;
}
.loading-bubble {
  background: #FFFFFF;
  color: #999;
}
.dot-loading {
  animation: blink 1.4s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.chat-input-area {
  display: flex;
  padding: 8px 12px;
  border-top: 1px solid var(--color-border);
  background: var(--color-card);
  gap: 8px;
  align-items: flex-end;
}
.chat-input {
  flex: 1;
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 15px;
  resize: none;
  max-height: 100px;
}
.chat-input::placeholder {
  color: var(--color-text-secondary);
}
.send-btn {
  height: 36px;
  padding: 0 16px;
  background: var(--color-primary);
  color: #141414;
  font-size: 15px;
  border-radius: 4px;
}
.send-btn:disabled {
  opacity: 0.5;
}

/* Markdown 样式 */
.message.assistant .bubble :deep(h1),
.message.assistant .bubble :deep(h2),
.message.assistant .bubble :deep(h3) {
  margin: 8px 0 4px;
  font-size: 16px;
}
.message.assistant .bubble :deep(p) {
  margin: 4px 0;
}
.message.assistant .bubble :deep(ul),
.message.assistant .bubble :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.message.assistant .bubble :deep(code) {
  background: #f0f0f0;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 13px;
}
.limit-overlay {
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
