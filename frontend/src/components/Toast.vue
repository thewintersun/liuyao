<template>
  <div class="toast-container">
    <transition-group name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['toast-item', `toast-${toast.type}`, { 'toast-hide': !toast.visible }]"
      >
        <span class="toast-icon">{{ iconMap[toast.type] }}</span>
        <span class="toast-msg">{{ toast.message }}</span>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getToasts } from '../utils/toast.js'

const toasts = computed(() => getToasts())

const iconMap = {
  success: '\u2714',
  error: '\u2716',
  warning: '\u26A0',
  info: '\u2139'
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 99998;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  pointer-events: none;
  width: 90%;
  max-width: 400px;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 2px;
  font-size: 15px;
  line-height: 1.4;
  pointer-events: auto;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  transition: opacity 0.3s, transform 0.3s;
  word-break: break-word;
}

.toast-hide {
  opacity: 0;
  transform: translateY(-10px);
}

.toast-icon {
  flex-shrink: 0;
  font-size: 16px;
}

.toast-msg {
  flex: 1;
}

/* 类型配色 — 与暗色中国风主题协调 */
.toast-success {
  background-color: rgba(34, 50, 28, 0.95);
  border: 1px solid rgba(89, 179, 0, 0.6);
  color: #b5e685;
}
.toast-success .toast-icon { color: #59B300; }

.toast-error {
  background-color: rgba(50, 24, 24, 0.95);
  border: 1px solid rgba(255, 68, 68, 0.6);
  color: #ff9999;
}
.toast-error .toast-icon { color: #FF4444; }

.toast-warning {
  background-color: rgba(50, 42, 20, 0.95);
  border: 1px solid rgba(249, 212, 124, 0.6);
  color: #F9D47C;
}
.toast-warning .toast-icon { color: #EBBD59; }

.toast-info {
  background-color: rgba(32, 32, 32, 0.95);
  border: 1px solid rgba(249, 212, 124, 0.5);
  color: #D9D9D9;
}
.toast-info .toast-icon { color: #F9D47C; }

/* 过渡动画 */
.toast-enter-active {
  transition: opacity 0.3s, transform 0.3s;
}
.toast-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
