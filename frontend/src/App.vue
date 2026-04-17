<template>
  <!-- 微信内置浏览器引导遮罩 -->
  <div v-if="showWechatGuide" class="wechat-guide-overlay" @click="showWechatGuide = false">
    <div class="wechat-guide-arrow">
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
        <path d="M20 36V8" stroke="#F9D47C" stroke-width="3" stroke-linecap="round"/>
        <path d="M8 20L20 6L32 20" stroke="#F9D47C" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div class="wechat-guide-content">
      <div class="wechat-guide-step">
        <span class="wechat-guide-num">1</span>
        点击右上角 <span class="wechat-guide-highlight">···</span> 按钮
      </div>
      <div class="wechat-guide-step">
        <span class="wechat-guide-num">2</span>
        选择 <span class="wechat-guide-highlight">在浏览器中打开</span>
      </div>
      <div class="wechat-guide-tip">点击任意位置关闭提示</div>
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

const showWechatGuide = ref(false)

onMounted(() => {
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('micromessenger')) {
    showWechatGuide.value = true
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

.wechat-guide-tip {
  color: #888;
  font-size: 14px;
  margin-top: 40px;
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
