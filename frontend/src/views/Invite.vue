<template>
  <div class="page invite-page">
    <div class="invite-card">
      <h3 class="card-title">{{ $t('我的邀请码') }}</h3>
      <div class="code-row">
        <span class="invite-code">{{ inviteCode || '...' }}</span>
        <button class="copy-btn" @click="copyCode">{{ $t('复制') }}</button>
      </div>
    </div>

    <div class="invite-card">
      <h3 class="card-title">{{ $t('邀请链接') }}</h3>
      <p class="invite-link-text">{{ inviteLink }}</p>
      <button class="btn-primary" @click="copyLink">{{ $t('复制邀请链接') }}</button>
    </div>

    <div class="invite-card">
      <h3 class="card-title">{{ $t('奖励规则') }}</h3>
      <div class="rule-item">
        <span class="rule-label">{{ $t('好友点开链接') }}</span>
        <span class="rule-value">{{ $t('你获得') }} +{{ visitReward }} {{ $t('次额度') }}</span>
      </div>
      <div class="rule-item">
        <span class="rule-label">{{ $t('好友注册成功') }}</span>
        <span class="rule-value">{{ $t('双方各获') }} +{{ registerReward }} {{ $t('次额度') }}</span>
      </div>
    </div>

    <div class="invite-card">
      <h3 class="card-title">{{ $t('本月统计') }}</h3>
      <div class="stats-row">
        <div class="stat-item">
          <span class="stat-value">{{ monthlyCount }}</span>
          <span class="stat-label">{{ $t('已邀请') }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ monthlyReward }}</span>
          <span class="stat-label">{{ $t('获得额度') }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ monthlyLimit }}</span>
          <span class="stat-label">{{ $t('月度上限') }}</span>
        </div>
      </div>
    </div>

    <div class="invite-card" v-if="records.length > 0">
      <h3 class="card-title">{{ $t('邀请记录') }}</h3>
      <div class="record-item" v-for="(item, index) in records" :key="index">
        <div class="record-left">
          <span class="record-type" :class="item.type">{{ item.type === 'visit' ? $t('访问') : $t('注册') }}</span>
          <span class="record-name">{{ item.invitee_name || maskIp(item.visitor_ip) }}</span>
        </div>
        <div class="record-right">
          <span class="record-reward">+{{ item.reward }}</span>
          <span class="record-time">{{ formatTime(item.created_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getInviteStats, getQuotaConfig } from '../api/index.js'
import { t } from '../utils/locale.js'

const inviteCode = ref('')
const inviteLink = ref('')
const visitReward = ref(5)
const registerReward = ref(20)
const monthlyCount = ref(0)
const monthlyReward = ref(0)
const monthlyLimit = ref(20)
const records = ref([])

onMounted(async () => {
  try {
    const [statsRes, quotaRes] = await Promise.all([
      getInviteStats(),
      getQuotaConfig()
    ])
    inviteCode.value = statsRes.invite_code || ''
    inviteLink.value = location.origin + '/?ref=' + inviteCode.value
    monthlyCount.value = statsRes.monthly_count || 0
    monthlyReward.value = statsRes.monthly_reward || 0
    monthlyLimit.value = statsRes.monthly_limit || 20
    records.value = statsRes.records || []
    visitReward.value = quotaRes.invite_visit_reward || 5
    registerReward.value = quotaRes.invite_register_reward || 20
  } catch (e) {
    console.error('加载邀请数据失败', e)
  }
})

function copyCode() {
  copyText(inviteCode.value)
}

function copyLink() {
  copyText(inviteLink.value)
}

function copyText(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      alert(t('已复制到剪贴板'))
    }).catch(() => fallbackCopy(text))
  } else {
    fallbackCopy(text)
  }
}

function fallbackCopy(text) {
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.position = 'fixed'
  ta.style.opacity = '0'
  document.body.appendChild(ta)
  ta.select()
  document.execCommand('copy')
  document.body.removeChild(ta)
  alert(t('已复制到剪贴板'))
}

function maskIp(ip) {
  if (!ip) return '-'
  const parts = ip.split('.')
  if (parts.length === 4) {
    return parts[0] + '.' + parts[1] + '.*.*'
  }
  return ip
}

function formatTime(timeStr) {
  if (!timeStr) return ''
  return timeStr.replace('T', ' ').substring(0, 16)
}
</script>

<style scoped>
.invite-page {
  padding-bottom: 20px;
}
.invite-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 16px;
  margin-bottom: 12px;
}
.card-title {
  color: var(--color-primary);
  font-size: 16px;
  margin-bottom: 12px;
}
.code-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.invite-code {
  font-size: 28px;
  font-weight: bold;
  color: var(--color-text);
  letter-spacing: 4px;
  font-family: 'Courier New', monospace;
}
.copy-btn {
  padding: 6px 16px;
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
}
.invite-link-text {
  color: var(--color-text-secondary);
  font-size: 13px;
  word-break: break-all;
  margin-bottom: 12px;
}
.rule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(249,212,124,0.1);
}
.rule-item:last-child {
  border-bottom: none;
}
.rule-label {
  color: var(--color-text);
  font-size: 14px;
}
.rule-value {
  color: var(--color-primary);
  font-size: 14px;
}
.stats-row {
  display: flex;
  justify-content: space-around;
  text-align: center;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-value {
  color: var(--color-primary);
  font-size: 24px;
  font-weight: bold;
}
.stat-label {
  color: var(--color-text-secondary);
  font-size: 13px;
}
.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(249,212,124,0.1);
}
.record-item:last-child {
  border-bottom: none;
}
.record-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.record-type {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}
.record-type.visit {
  background: rgba(249,212,124,0.15);
  color: var(--color-primary);
}
.record-type.register {
  background: rgba(76,175,80,0.15);
  color: #4CAF50;
}
.record-name {
  color: var(--color-text);
  font-size: 14px;
}
.record-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}
.record-reward {
  color: var(--color-primary);
  font-size: 14px;
  font-weight: bold;
}
.record-time {
  color: var(--color-text-secondary);
  font-size: 12px;
}
</style>
