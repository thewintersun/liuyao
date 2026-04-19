<template>
  <!-- 微信内置浏览器引导遮罩 -->
  <div v-if="showWechatGuide" class="wechat-guide-overlay">
    <div class="wechat-guide-arrow">
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
        <path d="M20 36V8" stroke="#F9D47C" stroke-width="3" stroke-linecap="round"/>
        <path d="M8 20L20 6L32 20" stroke="#F9D47C" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div class="wechat-guide-content">
      <p class="wechat-guide-title">推荐使用系统浏览器打开</p>
      <p class="wechat-guide-subtitle">体验更流畅，功能更完整</p>
      <div class="wechat-guide-step">
        <span class="wechat-guide-num">1</span>
        点击右上角 <span class="wechat-guide-highlight">···</span> 按钮
      </div>
      <div class="wechat-guide-step">
        <span class="wechat-guide-num">2</span>
        选择 <span class="wechat-guide-highlight">在浏览器中打开</span>
      </div>
      <button class="wechat-guide-continue" @click="showWechatGuide = false">继续使用当前浏览器</button>
    </div>
  </div>

  <div class="app-container">
    <div class="app-content">
      <NavBar />
      <div class="page-content">
        <router-view />
      </div>
      <TabBar />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TabBar from './components/TabBar.vue'
import NavBar from './components/NavBar.vue'
import { reportInviteVisit } from './api/index.js'

const showWechatGuide = ref(false)

onMounted(() => {
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('micromessenger')) {
    showWechatGuide.value = true
  }

  // 检测邀请链接参数 ?ref=XXXXXX
  const urlParams = new URLSearchParams(window.location.search)
  const refCode = urlParams.get('ref')
  if (refCode) {
    sessionStorage.setItem('liuyao_ref_code', refCode)
    // 通知后端（游客访问奖励）
    reportInviteVisit(refCode).catch(() => {})
    // 清除 URL 中的 ref 参数
    urlParams.delete('ref')
    const newSearch = urlParams.toString()
    const newUrl = window.location.pathname + (newSearch ? '?' + newSearch : '') + window.location.hash
    history.replaceState(null, '', newUrl)
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: var(--color-bg);
  display: flex;
  justify-content: center;
}
.app-content {
  width: 100%;
  max-width: 480px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
}
.page-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 60px;
}

/* 微信引导遮罩 */
.wechat-guide-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.85);
  z-index: 99999;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding-top: 20px;
  padding-right: 24px;
}

.wechat-guide-arrow {
  animation: arrowBounce 1.2s ease-in-out infinite;
}

@keyframes arrowBounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.wechat-guide-content {
  margin-top: 30px;
  margin-right: 0;
  text-align: center;
  width: 100%;
  padding: 0 24px;
}

.wechat-guide-title {
  color: #fff;
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 6px;
}

.wechat-guide-subtitle {
  color: #aaa;
  font-size: 14px;
  margin-bottom: 28px;
}

.wechat-guide-step {
  color: #fff;
  font-size: 20px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.wechat-guide-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: var(--color-primary);
  color: #141414;
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
}

.wechat-guide-highlight {
  color: var(--color-primary);
  font-weight: bold;
}

.wechat-guide-continue {
  margin-top: 40px;
  background: transparent;
  color: #666;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 10px 24px;
  font-size: 14px;
  cursor: pointer;
}

/* PC 端宽屏适配 */
@media (min-width: 768px) {
  .app-content {
    max-width: 640px;
  }
}
@media (min-width: 1200px) {
  .app-content {
    max-width: 768px;
  }
}
</style>
