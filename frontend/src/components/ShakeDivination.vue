<template>
  <div class="shake-divination">
    <!-- 进度条: 6个爻位 -->
    <div class="progress-section">
      <div class="progress-label">{{ phase === 'done' ? '摇卦完成' : `第 ${ currentStep + 1 } / 6 次` }}</div>
      <div class="progress-bar">
        <div
          v-for="i in 6"
          :key="i"
          class="progress-slot"
          :class="{
            completed: i - 1 < currentStep,
            current: i - 1 === currentStep && phase !== 'done',
            pending: i - 1 > currentStep
          }"
        >
          <span v-if="i - 1 < currentStep" class="slot-symbol">
            {{ yaoValues[i - 1] === 1 || yaoValues[i - 1] === 3 ? '▅▅▅' : '▅ ▅' }}
          </span>
          <span v-else-if="i - 1 === currentStep && phase !== 'done'" class="slot-symbol current-symbol">?</span>
          <span v-else class="slot-symbol pending-symbol">—</span>
        </div>
      </div>
    </div>

    <!-- 铜钱区域 (非完成状态显示) -->
    <div v-if="phase !== 'done'" class="coins-section">
      <div class="coins-container">
        <div
          v-for="(coin, idx) in coinResults"
          :key="idx"
          class="coin-wrapper"
        >
          <div
            class="coin"
            :class="{
              'coin-spinning': phase === 'animating',
              'coin-heads': phase === 'result' && coin === '正',
              'coin-tails': phase === 'result' && coin === '背'
            }"
            :style="phase === 'animating' ? { animationDelay: (idx * 0.15) + 's' } : {}"
          >
            <div class="coin-face coin-front">正</div>
            <div class="coin-face coin-back">背</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 状态提示区 (固定高度，避免按钮跳动) -->
    <div v-if="phase !== 'done'" class="status-area">
      <!-- 结果文字 -->
      <div v-if="phase === 'result'" class="result-text">
        <span class="result-value">{{ resultLabels[currentYaoValue] }}</span>
      </div>
      <!-- 摇卦中提示 -->
      <div v-else-if="phase === 'animating'" class="animating-hint">
        摇卦中...
      </div>
      <!-- 移动端: 未激活时的提示 -->
      <div v-else-if="isMobile && !motionActivated" class="shake-prompt">
        <p class="shake-hint-sub">点击下方按钮启用摇晃感应</p>
        <p class="shake-hint-sub">之后摇动手机即可起卦</p>
      </div>
      <!-- 移动端摇晃提示 -->
      <div v-else-if="isMobile && motionActivated && phase === 'idle'" class="shake-prompt">
        <div class="shake-icon">📳</div>
        <p class="shake-hint-main">集中精神默想所问之事</p>
        <p class="shake-hint-sub">摇动手机起卦</p>
      </div>
    </div>

    <!-- 操作按钮区域 (非完成状态) -->
    <div v-if="phase !== 'done'" class="action-section">
      <!-- 移动端: 需要先获取权限 -->
      <template v-if="isMobile && !motionActivated">
        <button
          class="btn-primary action-btn"
          @click="activateMotion"
        >启用摇晃感应</button>
      </template>
      <!-- 移动端: 已获取权限 -->
      <template v-else-if="isMobile && motionActivated">
        <button
          v-if="phase === 'result'"
          class="btn-primary action-btn"
          @click="confirmStep"
        >{{ currentStep < 5 ? '确认，下一爻' : '确认' }}</button>
      </template>
      <!-- 桌面端 -->
      <template v-else>
        <p v-if="phase === 'idle'" class="desktop-hint">集中精神默想所问之事</p>
        <button
          v-if="phase === 'idle'"
          class="btn-primary action-btn"
          @click="doThrow"
        >点击摇卦</button>
        <button
          v-else-if="phase === 'result'"
          class="btn-primary action-btn"
          @click="confirmStep"
        >{{ currentStep < 5 ? '确认，下一爻' : '确认' }}</button>
      </template>
    </div>

    <!-- 摇卦结果汇总 (完成状态) -->
    <div v-if="phase === 'done'" class="summary-section card">
      <div class="summary-title">摇卦结果</div>
      <div class="summary-rows">
        <div
          v-for="i in 6"
          :key="i"
          class="summary-row"
        >
          <span class="summary-label">第{{ i }}次摇</span>
          <span class="summary-value">{{ resultLabels[yaoValues[i - 1]] }}</span>
        </div>
      </div>
      <button class="btn-primary action-btn summary-btn" @click="emitComplete">开始排盘</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  dateInfo: Object
})
const emit = defineEmits(['complete'])
const router = useRouter()

// 移动设备检测
const isMobile = ref(false)
// 权限是否已激活（移动端通过用户点击获取权限后为 true）
const motionActivated = ref(false)
// 设备动作检测
const motionSupported = ref(false)

// 摇动检测变量
let lastShakeTime = 0
let lastAccel = { x: 0, y: 0, z: 0 }

// 防止 iOS 摇动撤销 (Shake to Undo) — 安全网
function preventUndo(e) {
  if (e.inputType === 'historyUndo' || e.inputType === 'historyRedo') {
    e.preventDefault()
  }
}

// 爻值编码: 0=无背(老阴), 1=一背(少阳), 2=二背(少阴), 3=三背(老阳)
const resultLabels = {
  0: '无背 — 老阴 ▅▅ ▅▅',
  1: '一背 — 少阳 ▅▅▅▅▅',
  2: '二背 — 少阴 ▅▅ ▅▅',
  3: '三背 — 老阳 ▅▅▅▅▅',
}

// 状态机: 'idle' → 'animating' → 'result' → 'idle'(下一步) 或 'done'(第6次后)
const phase = ref('idle')
const currentStep = ref(0)
const yaoValues = reactive([0, 0, 0, 0, 0, 0])
const coinResults = reactive(['正', '正', '正'])
const currentYaoValue = ref(0)

// ====== 铜钱摇晃音效 ======
let shakeAudio = null

function playShakeSound() {
  try {
    if (!shakeAudio) {
      shakeAudio = new Audio('/universfield-spinning-coin-on-table-352448.mp3')
    }
    shakeAudio.currentTime = 0
    shakeAudio.play()
  } catch {
    // 音频不可用时静默降级
  }
}

// 掷铜钱逻辑
function throwCoins() {
  const results = [
    Math.random() < 0.5 ? '正' : '背',
    Math.random() < 0.5 ? '正' : '背',
    Math.random() < 0.5 ? '正' : '背',
  ]
  const backs = results.filter(c => c === '背').length
  return { coins: results, yaoValue: backs }
}

// 执行掷卦
function doThrow() {
  if (phase.value !== 'idle') return

  const { coins, yaoValue } = throwCoins()

  // 播放摇晃音效
  playShakeSound()

  // 先设置为动画状态 (铜钱旋转)
  phase.value = 'animating'

  // 动画结束后显示结果
  // 动画时长: 1.2s 基础 + 0.3s 最大延迟 + 0.1s 缓冲
  setTimeout(() => {
    // 更新铜钱结果
    coinResults[0] = coins[0]
    coinResults[1] = coins[1]
    coinResults[2] = coins[2]
    currentYaoValue.value = yaoValue

    phase.value = 'result'
  }, 1900)
}

// 确认当前步骤
function confirmStep() {
  if (phase.value !== 'result') return

  yaoValues[currentStep.value] = currentYaoValue.value

  if (currentStep.value >= 5) {
    // 六次摇卦完成 — 移除 devicemotion 监听，避免干扰后续按钮点击
    window.removeEventListener('devicemotion', handleMotion)
    currentStep.value = 6
    phase.value = 'done'
  } else {
    // 进入下一步
    currentStep.value++
    lastShakeTime = Date.now()  // 重置防抖，避免点击确认的振动误触发
    phase.value = 'idle'
  }
}

// 完成：保存数据并跳转排盘页
function emitComplete() {
  const values = [yaoValues[0], yaoValues[1], yaoValues[2], yaoValues[3], yaoValues[4], yaoValues[5]]
  emit('complete', values)

  // 直接处理导航，不依赖 emit 回调（微信 X5 等内置浏览器中 emit 可能不触发父组件）
  try {
    sessionStorage.removeItem('liuyao_currentRecordId')
    if (props.dateInfo) {
      sessionStorage.setItem('liuyao_date', JSON.stringify(props.dateInfo))
    }
    sessionStorage.setItem('liuyao_yaoValues', JSON.stringify(values))
  } catch (e) { /* ignore */ }

  router.push('/hexagram').catch(() => {
    // router.push 失败时使用 location 兜底
    window.location.href = '/hexagram'
  })
}

// 设备动作事件处理
function handleMotion(event) {
  if (phase.value !== 'idle') return

  const accel = event.accelerationIncludingGravity
  if (!accel || accel.x == null) return

  const deltaX = Math.abs(accel.x - lastAccel.x)
  const deltaY = Math.abs(accel.y - lastAccel.y)
  const deltaZ = Math.abs(accel.z - lastAccel.z)
  const totalDelta = deltaX + deltaY + deltaZ

  lastAccel = { x: accel.x, y: accel.y, z: accel.z }

  // 预防 iOS "摇动撤销": 当检测到手机开始晃动时，立即移除输入焦点
  // 阈值设为摇卦阈值的一半，确保在 iOS 系统检测到摇动之前就已 blur
  if (totalDelta > 15) {
    document.activeElement?.blur()
  }

  // 摇动阈值: 总变化量 > 30, 防抖 1.5 秒
  const now = Date.now()
  if (totalDelta > 30 && now - lastShakeTime > 500) {
    lastShakeTime = now
    doThrow()
  }
}

// 检测是否为移动设备
function detectMobile() {
  const ua = navigator.userAgent || ''
  return /Android|iPhone|iPad|iPod|webOS|BlackBerry|IEMobile|Opera Mini/i.test(ua)
    || ('ontouchstart' in window && navigator.maxTouchPoints > 1)
}

// 移动端: 用户点击按钮后请求权限并启动监听（必须在用户手势中调用）
async function activateMotion() {
  if (!('DeviceMotionEvent' in window)) {
    // 设备不支持，降级为点击模式
    isMobile.value = false
    return
  }

  // iOS 13+ 需要显式请求权限
  if (typeof DeviceMotionEvent.requestPermission === 'function') {
    try {
      const permission = await DeviceMotionEvent.requestPermission()
      if (permission !== 'granted') {
        // 用户拒绝权限，降级为点击模式
        isMobile.value = false
        return
      }
    } catch {
      // 权限请求失败，降级为点击模式
      isMobile.value = false
      return
    }
  }

  motionSupported.value = true
  motionActivated.value = true
  window.addEventListener('devicemotion', handleMotion)

  // 防止 iOS "摇动撤销": 移除当前焦点
  document.activeElement?.blur()
  document.addEventListener('beforeinput', preventUndo)
}

// 桌面端: 尝试直接启动（不需要权限请求的环境）
function initMotionDesktop() {
  if (!('DeviceMotionEvent' in window)) return
  // 桌面端如果支持 DeviceMotion（如带陀螺仪的笔记本），直接监听
  if (typeof DeviceMotionEvent.requestPermission !== 'function') {
    motionSupported.value = true
    window.addEventListener('devicemotion', handleMotion)
  }
}

// 生命周期钩子
onMounted(() => {
  isMobile.value = detectMobile()
  if (!isMobile.value) {
    initMotionDesktop()
  }
})

onUnmounted(() => {
  window.removeEventListener('devicemotion', handleMotion)
  document.removeEventListener('beforeinput', preventUndo)
})

// 暴露 motionSupported 供外部使用
defineExpose({ motionSupported })
</script>

<style scoped>
.shake-divination {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 0;
  gap: 24px;
}

/* ======= 进度条 ======= */
.progress-section {
  width: 100%;
}

.progress-label {
  text-align: center;
  color: var(--color-primary);
  font-size: 16px;
  margin-bottom: 12px;
}

.progress-bar {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.progress-slot {
  width: 52px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
  border: 1px solid var(--color-border);
  background: var(--color-card);
  transition: all 0.3s ease;
}

.progress-slot.completed {
  background: #2a2a1e;
  border-color: var(--color-primary);
}

.progress-slot.current {
  border-color: var(--color-primary);
  box-shadow: 0 0 8px rgba(249, 212, 124, 0.5);
}

.progress-slot.pending {
  background: #1a1a1a;
  border-color: #333;
}

.slot-symbol {
  font-size: 12px;
  line-height: 1;
  letter-spacing: 0;
}

.progress-slot.completed .slot-symbol {
  color: var(--color-primary);
}

.current-symbol {
  color: var(--color-primary);
  font-size: 16px;
  font-weight: bold;
}

.pending-symbol {
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* ======= 铜钱区域 ======= */
.coins-section {
  padding: 20px 0;
}

.coins-container {
  display: flex;
  gap: 20px;
  justify-content: center;
  perspective: 800px;
}

.coin-wrapper {
  width: 72px;
  height: 72px;
  perspective: 800px;
}

.coin {
  width: 72px;
  height: 72px;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.3s ease;
}

.coin-face {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  backface-visibility: hidden;
  border: 2px solid #b8860b;
  background: linear-gradient(145deg, #F9D47C, #d4a843);
  color: #8b0000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4), inset 0 1px 2px rgba(255, 255, 255, 0.3);
}

.coin-back {
  transform: rotateY(180deg);
}

/* 旋转动画 */
.coin-spinning {
  animation: coinSpin 1.5s ease-in-out forwards;
}

@keyframes coinSpin {
  0% {
    transform: rotateY(0deg) translateY(0px);
  }
  15% {
    transform: rotateY(540deg) translateY(-30px);
  }
  30% {
    transform: rotateY(1080deg) translateY(-15px);
  }
  50% {
    transform: rotateY(1440deg) translateY(-25px);
  }
  70% {
    transform: rotateY(1620deg) translateY(-10px);
  }
  85% {
    transform: rotateY(1740deg) translateY(-5px);
  }
  100% {
    transform: rotateY(1800deg) translateY(0px);
  }
}

/* 结果状态: 正面朝上 (rotateY(0)) */
.coin-heads {
  transform: rotateY(0deg);
}

/* 结果状态: 背面朝上 (rotateY(180)) */
.coin-tails {
  transform: rotateY(180deg);
}

/* ======= 结果文字 ======= */
.result-text {
  text-align: center;
  padding: 8px 0;
}

.result-value {
  color: var(--color-primary);
  font-size: 18px;
  font-weight: 500;
}

/* ======= 状态提示区 (固定高度) ======= */
.status-area {
  width: 100%;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.animating-hint {
  color: var(--color-primary);
  font-size: 16px;
  text-align: center;
  letter-spacing: 2px;
}

/* ======= 操作按钮 ======= */
.action-section {
  width: 100%;
  min-height: 50px;
  padding: 0 16px;
}

.shake-hint {
  color: var(--color-text-secondary);
  font-size: 14px;
  text-align: center;
  margin-bottom: 12px;
}

.shake-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 0;
}

.shake-icon {
  font-size: 48px;
  animation: shakeWobble 1.5s ease-in-out infinite;
}

@keyframes shakeWobble {
  0%, 100% { transform: rotate(0deg); }
  15% { transform: rotate(-12deg); }
  30% { transform: rotate(12deg); }
  45% { transform: rotate(-8deg); }
  60% { transform: rotate(8deg); }
  75% { transform: rotate(-4deg); }
  90% { transform: rotate(4deg); }
}

.shake-hint-main {
  color: var(--color-primary);
  font-size: 20px;
  font-weight: 500;
}

.shake-hint-sub {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.desktop-hint {
  color: var(--color-text-secondary);
  font-size: 16px;
  text-align: center;
  margin: 0 0 8px;
}
.action-btn {
  width: 100%;
  height: 50px;
  font-size: 18px;
  border-radius: 1px;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ======= 结果汇总 ======= */
.summary-section {
  width: 100%;
}

.summary-title {
  text-align: center;
  color: var(--color-primary);
  font-size: 20px;
  font-weight: 500;
  margin-bottom: 16px;
}

.summary-rows {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(249, 212, 124, 0.15);
}

.summary-row:last-child {
  border-bottom: none;
}

.summary-label {
  color: var(--color-text-secondary);
  font-size: 15px;
}

.summary-value {
  color: var(--color-text);
  font-size: 15px;
}

.summary-btn {
  margin-top: 20px;
}
</style>
