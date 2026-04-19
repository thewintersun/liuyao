import axios from 'axios'
import { getLang } from '../utils/locale.js'

const api = axios.create({
  timeout: 300000
})

// 请求拦截器：附加 token + 语言
api.interceptors.request.use(config => {
  const token = localStorage.getItem('liuyao_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  config.headers['X-Lang'] = getLang()
  return config
})

// 响应拦截器：处理 401
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('liuyao_token')
      localStorage.removeItem('liuyao_user')
    }
    return Promise.reject(error)
  }
)

async function requestWithRetry(config, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await api(config)
      return response.data
    } catch (error) {
      if (i === maxRetries - 1) throw error
      // 不重试 4xx 错误
      if (error.response && error.response.status >= 400 && error.response.status < 500) throw error
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  }
}

// ========== 认证接口 ==========

export async function getCaptcha() {
  const response = await api.get('/api/captcha')
  return response.data
}

export async function register(username, password, email, captchaId, captchaText, agreed = false, inviteCode = '') {
  const data = { username, password, email, captcha_id: captchaId, captcha_text: captchaText, agreed }
  if (inviteCode) data.invite_code = inviteCode
  const response = await api.post('/api/auth/register', data)
  return response.data
}

export async function login(username, password) {
  const response = await api.post('/api/auth/login', { username, password })
  return response.data
}

export async function getUserInfo() {
  const response = await api.get('/api/auth/me')
  return response.data
}

export async function getQuotaConfig() {
  const response = await api.get('/api/config/quota')
  return response.data
}

export async function changePassword(oldPassword, newPassword) {
  const response = await api.put('/api/auth/change-password', {
    old_password: oldPassword, new_password: newPassword
  })
  return response.data
}

export async function changeEmail(email) {
  const response = await api.put('/api/auth/change-email', { email })
  return response.data
}

export async function forgotPassword(email) {
  const response = await api.post('/api/auth/forgot-password', { email })
  return response.data
}

export async function verifyResetToken(token) {
  const response = await api.get(`/api/auth/verify-reset-token/${token}`)
  return response.data
}

export async function resetPassword(token, password) {
  const response = await api.post('/api/auth/reset-password', { token, password })
  return response.data
}

// ========== 业务接口 ==========

// 轮询异步任务结果，每 2 秒查询一次，最多 5 分钟
async function pollTaskResult(taskId, maxWait = 300000) {
  const start = Date.now()
  while (Date.now() - start < maxWait) {
    await new Promise(resolve => setTimeout(resolve, 5000))
    const res = await api.get(`/api/task/${taskId}`)
    if (res.data.status !== 'processing') {
      return res.data
    }
  }
  throw new Error('timeout')
}

export async function submitHexagram(guaXiangInfo, background, category) {
  // 异步提交 + 轮询，兼容微信 WebView 等短超时环境
  const submitRes = await api.post('/api/receive/async', {
    gua_xiang_info: guaXiangInfo,
    background: background,
    category: category
  })
  if (submitRes.data.task_id) {
    return pollTaskResult(submitRes.data.task_id)
  }
  return submitRes.data
}

export async function chatMessage(sessionId, message) {
  const submitRes = await api.post('/api/chat/async', {
    session_id: sessionId,
    message: message
  })
  if (submitRes.data.task_id) {
    return pollTaskResult(submitRes.data.task_id)
  }
  return submitRes.data
}

export async function restoreChat(sessionId, messages) {
  const response = await api.post('/api/chat/restore', { session_id: sessionId, messages })
  return response.data
}

export async function submitFeedback(feedback, contact) {
  return requestWithRetry({
    method: 'post',
    url: '/api/feedback',
    data: {
      feedback: feedback,
      contact: contact || '未提供'
    }
  })
}

// ========== 邀请接口 ==========

export async function reportInviteVisit(code) {
  const response = await api.post('/api/invite/visit', { code })
  return response.data
}

export async function getInviteStats() {
  const response = await api.get('/api/invite/stats')
  return response.data
}

// ========== 记录接口 ==========

export async function fetchRecords() {
  const response = await api.get('/api/records')
  return response.data
}

export async function createServerRecord(data) {
  const response = await api.post('/api/records', data)
  return response.data
}

export async function updateServerRecord(id, data) {
  const response = await api.put(`/api/records/${id}`, data)
  return response.data
}

export async function deleteServerRecord(id) {
  const response = await api.delete(`/api/records/${id}`)
  return response.data
}

// ========== 管理接口 ==========

export async function getAdminDashboard() {
  const response = await api.get('/api/admin/dashboard')
  return response.data
}

export async function getAdminUsers(page = 1, perPage = 20, search = '') {
  const params = { page, per_page: perPage }
  if (search) params.search = search
  const response = await api.get('/api/admin/users', { params })
  return response.data
}

export async function getAdminUserDetail(userId) {
  const response = await api.get(`/api/admin/users/${userId}`)
  return response.data
}

export async function updateUserQuota(userId, freeUses) {
  const response = await api.put(`/api/admin/users/${userId}/quota`, { free_uses: freeUses })
  return response.data
}

export async function banUser(userId) {
  const response = await api.put(`/api/admin/users/${userId}/ban`)
  return response.data
}

export async function unbanUser(userId) {
  const response = await api.put(`/api/admin/users/${userId}/unban`)
  return response.data
}

export async function getAdminConfig() {
  const response = await api.get('/api/admin/config')
  return response.data
}

export async function updateAdminConfig(config) {
  const response = await api.put('/api/admin/config', config)
  return response.data
}

export async function getAdminPrompts() {
  const response = await api.get('/api/admin/prompts')
  return response.data
}

export async function updateAdminPrompts(prompts) {
  const response = await api.put('/api/admin/prompts', prompts)
  return response.data
}

export async function getAdminFeedback(page = 1, perPage = 20, status = '') {
  const params = { page, per_page: perPage }
  if (status) params.status = status
  const response = await api.get('/api/admin/feedback', { params })
  return response.data
}

export async function updateFeedbackStatus(feedbackId, status) {
  const response = await api.put(`/api/admin/feedback/${feedbackId}`, { status })
  return response.data
}

export async function getAdminLogs(page = 1, perPage = 20, filters = {}) {
  const params = { page, per_page: perPage, ...filters }
  const response = await api.get('/api/admin/logs', { params })
  return response.data
}

export async function getSessionDetail(sessionId) {
  const response = await api.get(`/api/admin/logs/session/${sessionId}`)
  return response.data
}

export async function adminResetPassword(userId, password) {
  const response = await api.put(`/api/admin/users/${userId}/reset-password`, { password })
  return response.data
}
