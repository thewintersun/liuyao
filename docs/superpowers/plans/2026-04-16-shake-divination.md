# 摇动起卦 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "shake to divine" mode to the YaoInput page, allowing users to generate yao values via phone shake or button click with 3D coin flip animations.

**Architecture:** Extract the shake mode into a dedicated `ShakeDivination.vue` component to keep YaoInput.vue focused. The parent handles mode switching and the shared time picker; the child handles the complete shake experience (coins, animation, progress, device motion). The child emits completed yaoValues in the same `[0-3, 0-3, ...]` format, ensuring zero changes downstream.

**Tech Stack:** Vue 3 Composition API, CSS 3D transforms, DeviceMotionEvent API, Math.random()

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `frontend/src/components/ShakeDivination.vue` | Complete shake mode: 3D coins, progress bar, device motion, step-by-step flow, result summary |
| Modify | `frontend/src/views/YaoInput.vue` | Add mode toggle tabs, conditionally render manual mode vs `<ShakeDivination>`, pass time data on complete |

---

### Task 1: Create ShakeDivination component skeleton with progress bar

**Files:**
- Create: `frontend/src/components/ShakeDivination.vue`

- [ ] **Step 1: Create component with progress bar UI**

```vue
<template>
  <div class="shake-divination">
    <!-- 进度区: 6个爻位格 -->
    <div class="progress-label">第 {{ currentStep + 1 }} / 6 次</div>
    <div class="progress-bar">
      <div
        v-for="(slot, i) in 6"
        :key="i"
        class="progress-slot"
        :class="{
          completed: i < currentStep,
          current: i === currentStep && !allDone,
          pending: i > currentStep
        }"
      >
        <template v-if="i < currentStep">
          <span v-if="yaoValues[i] === 1 || yaoValues[i] === 3">▅▅▅</span>
          <span v-else>▅ ▅</span>
        </template>
        <template v-else-if="i === currentStep && !allDone">?</template>
        <template v-else>—</template>
      </div>
    </div>

    <!-- 占位: 硬币区域 (Task 2 实现) -->
    <div class="coin-area">
      <p class="hint-text">硬币动画区域</p>
    </div>

    <!-- 占位: 操作按钮 (Task 4 实现) -->
    <div class="action-area">
      <button class="btn-primary" disabled>点击摇卦</button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'

const emit = defineEmits(['complete'])

const currentStep = ref(0)
const yaoValues = reactive([0, 0, 0, 0, 0, 0])
const allDone = computed(() => currentStep.value >= 6)
</script>

<style scoped>
.shake-divination {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.progress-label {
  color: var(--color-primary);
  font-size: 14px;
  margin-bottom: 8px;
  opacity: 0.7;
}
.progress-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 24px;
}
.progress-slot {
  width: 48px;
  height: 34px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-family: inherit;
  transition: all 0.3s ease;
}
.progress-slot.completed {
  background: #2a2a1e;
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
}
.progress-slot.current {
  background: #2a2a1e;
  border: 1px solid #b8860b;
  color: var(--color-primary);
  box-shadow: 0 0 8px rgba(249, 212, 124, 0.3);
}
.progress-slot.pending {
  background: #1a1a1a;
  border: 1px solid #333;
  color: #555;
}
.coin-area {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 160px;
  margin-bottom: 16px;
}
.hint-text {
  color: var(--color-text-secondary);
  font-size: 14px;
}
.action-area {
  width: 100%;
}
</style>
```

- [ ] **Step 2: Verify the file was created correctly**

Run: `node -e "const fs=require('fs'); const f=fs.readFileSync('frontend/src/components/ShakeDivination.vue','utf8'); console.log('Lines:', f.split('\\n').length); console.log('Has template:', f.includes('<template>')); console.log('Has script:', f.includes('<script setup>'))"`
Expected: Lines count > 80, Has template: true, Has script: true

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ShakeDivination.vue
git commit -m "feat: add ShakeDivination component skeleton with progress bar"
```

---

### Task 2: Add 3D coin animation

**Files:**
- Modify: `frontend/src/components/ShakeDivination.vue`

- [ ] **Step 1: Replace coin-area placeholder with 3D coins**

Replace the `<!-- 占位: 硬币区域 (Task 2 实现) -->` block and `.coin-area` in the template with:

```html
<!-- 硬币动画区 -->
<div class="coin-area">
  <div class="coins-container" :class="{ throwing: isAnimating }">
    <div
      v-for="(coin, i) in coinResults"
      :key="i"
      class="coin-wrapper"
      :style="{ animationDelay: (i * 0.15) + 's' }"
    >
      <div
        class="coin"
        :class="{
          'coin-flip': isAnimating,
          'coin-heads': !isAnimating && hasResult && coin === '正',
          'coin-tails': !isAnimating && hasResult && coin === '背'
        }"
      >
        <div class="coin-face coin-front">正</div>
        <div class="coin-face coin-back">背</div>
      </div>
    </div>
  </div>
  <div v-if="hasResult && !isAnimating" class="result-text">
    {{ resultLabel }}
  </div>
</div>
```

- [ ] **Step 2: Add coin-related reactive state to script**

Add to the `<script setup>` section, after the existing refs:

```javascript
const isAnimating = ref(false)
const hasResult = ref(false)
const coinResults = reactive(['正', '正', '正'])  // 当前3枚硬币结果
const currentYaoValue = ref(0)

// 结果文字映射
const yaoLabels = {
  0: '无背 — 老阴 ▅▅ ▅▅',
  1: '一背 — 少阳 ▅▅▅▅▅',
  2: '二背 — 少阴 ▅▅ ▅▅',
  3: '三背 — 老阳 ▅▅▅▅▅',
}
const resultLabel = computed(() => yaoLabels[currentYaoValue.value])
```

- [ ] **Step 3: Add 3D coin CSS**

Add to the `<style scoped>` section:

```css
.coins-container {
  display: flex;
  gap: 20px;
  justify-content: center;
  perspective: 800px;
}
.coin-wrapper {
  width: 72px;
  height: 72px;
}
.coin {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.3s ease;
}
.coin-face {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #8b0000;
  backface-visibility: hidden;
  border: 3px solid #b8860b;
}
.coin-front {
  background: linear-gradient(145deg, #F9D47C, #d4a843);
  box-shadow: 0 4px 15px rgba(249, 212, 124, 0.4);
}
.coin-back {
  background: linear-gradient(145deg, #d4a843, #b8860b);
  box-shadow: 0 4px 15px rgba(249, 212, 124, 0.3);
  transform: rotateY(180deg);
}

/* 翻转动画 */
.coin-flip {
  animation: coinFlip 1.2s ease-in-out forwards;
}
.coin-wrapper:nth-child(2) .coin-flip {
  animation-delay: 0.15s;
}
.coin-wrapper:nth-child(3) .coin-flip {
  animation-delay: 0.3s;
}

@keyframes coinFlip {
  0% { transform: rotateY(0deg) translateY(0); }
  15% { transform: rotateY(180deg) translateY(-40px); }
  30% { transform: rotateY(360deg) translateY(-60px); }
  50% { transform: rotateY(540deg) translateY(-50px); }
  70% { transform: rotateY(720deg) translateY(-20px); }
  85% { transform: rotateY(860deg) translateY(-5px); }
  100% { transform: rotateY(var(--final-rotation)) translateY(0); }
}

/* 落定状态: 正面朝上 */
.coin-heads {
  transform: rotateY(0deg);
}
/* 落定状态: 背面朝上 */
.coin-tails {
  transform: rotateY(180deg);
}

.result-text {
  color: var(--color-primary);
  font-size: 16px;
  margin-top: 16px;
  text-align: center;
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ShakeDivination.vue
git commit -m "feat: add 3D coin flip animation with CSS transforms"
```

---

### Task 3: Implement coin throw logic and step-by-step flow

**Files:**
- Modify: `frontend/src/components/ShakeDivination.vue`

- [ ] **Step 1: Add throwCoins and confirmStep functions**

Add to `<script setup>`, replacing any placeholder button logic:

```javascript
import { ref, reactive, computed, nextTick } from 'vue'

// 状态机: 'idle' → 'animating' → 'result' → 'idle'(next) or 'done'
const phase = ref('idle') // 'idle' | 'animating' | 'result' | 'done'

function throwCoins() {
  if (phase.value !== 'idle' || allDone.value) return

  // 生成随机结果
  const results = [
    Math.random() < 0.5 ? '正' : '背',
    Math.random() < 0.5 ? '正' : '背',
    Math.random() < 0.5 ? '正' : '背',
  ]
  const backs = results.filter(c => c === '背').length

  coinResults[0] = results[0]
  coinResults[1] = results[1]
  coinResults[2] = results[2]
  currentYaoValue.value = backs

  // 设置每枚硬币的最终旋转角度
  nextTick(() => {
    const wrappers = document.querySelectorAll('.coin-wrapper .coin')
    wrappers.forEach((el, i) => {
      // 正面=偶数*180, 背面=奇数*180
      const finalDeg = results[i] === '正' ? 720 + 360 : 720 + 540
      el.style.setProperty('--final-rotation', finalDeg + 'deg')
    })
  })

  // 开始动画
  phase.value = 'animating'
  isAnimating.value = true
  hasResult.value = false

  // 动画结束后切换到 result 状态
  setTimeout(() => {
    isAnimating.value = false
    hasResult.value = true
    phase.value = 'result'
  }, 1500)
}

function confirmStep() {
  if (phase.value !== 'result') return

  yaoValues[currentStep.value] = currentYaoValue.value
  currentStep.value++

  if (currentStep.value >= 6) {
    phase.value = 'done'
  } else {
    // 重置为 idle，准备下一次
    hasResult.value = false
    phase.value = 'idle'
  }
}

function submitResult() {
  emit('complete', [...yaoValues])
}
```

- [ ] **Step 2: Update template action-area**

Replace the `<!-- 占位: 操作按钮 (Task 4 实现) -->` block with:

```html
<!-- 操作区 -->
<div class="action-area">
  <!-- 等待摇卦 -->
  <template v-if="phase === 'idle'">
    <p v-if="motionSupported" class="shake-hint">{{ $t('摇动手机起卦') }}</p>
    <button class="btn-primary" @click="throwCoins">{{ $t('点击摇卦') }}</button>
  </template>

  <!-- 确认结果 -->
  <template v-else-if="phase === 'result'">
    <button class="btn-primary" @click="confirmStep">{{ $t('确认，下一爻') }}</button>
  </template>

  <!-- 动画播放中 -->
  <template v-else-if="phase === 'animating'">
    <button class="btn-primary" disabled style="opacity:0.5">{{ $t('摇卦中...') }}</button>
  </template>

  <!-- 全部完成 -->
  <template v-else-if="phase === 'done'">
    <div class="summary">
      <div class="summary-title">{{ $t('摇卦结果') }}</div>
      <div class="summary-rows">
        <div v-for="i in 6" :key="i" class="summary-row">
          <span class="summary-label">{{ $t('第' + i + '次摇') }}</span>
          <span class="summary-value">{{ yaoLabels[yaoValues[i - 1]] }}</span>
        </div>
      </div>
    </div>
    <button class="btn-primary" @click="submitResult" style="margin-top:16px">{{ $t('开始排盘') }}</button>
  </template>
</div>
```

- [ ] **Step 3: Add a placeholder ref for motion support**

Add to script (will be implemented in Task 4):

```javascript
const motionSupported = ref(false)
```

- [ ] **Step 4: Add summary CSS**

Add to `<style scoped>`:

```css
.shake-hint {
  color: var(--color-text-secondary);
  font-size: 14px;
  text-align: center;
  margin-bottom: 12px;
}
.summary {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 16px;
  width: 100%;
}
.summary-title {
  color: var(--color-primary);
  font-size: 16px;
  text-align: center;
  margin-bottom: 12px;
}
.summary-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid rgba(249, 212, 124, 0.1);
}
.summary-label {
  color: var(--color-text-secondary);
  font-size: 14px;
}
.summary-value {
  color: var(--color-primary);
  font-size: 14px;
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ShakeDivination.vue
git commit -m "feat: implement coin throw logic and step-by-step confirmation flow"
```

---

### Task 4: Add device motion shake detection

**Files:**
- Modify: `frontend/src/components/ShakeDivination.vue`

- [ ] **Step 1: Add shake detection logic**

Add to `<script setup>`, replacing the `motionSupported` placeholder and adding lifecycle hooks:

```javascript
import { ref, reactive, computed, nextTick, onMounted, onUnmounted } from 'vue'

const motionSupported = ref(false)
let lastShakeTime = 0
let lastAccel = { x: 0, y: 0, z: 0 }

function handleMotion(event) {
  if (phase.value !== 'idle' || allDone.value) return

  const accel = event.accelerationIncludingGravity
  if (!accel || accel.x == null) return

  const deltaX = Math.abs(accel.x - lastAccel.x)
  const deltaY = Math.abs(accel.y - lastAccel.y)
  const deltaZ = Math.abs(accel.z - lastAccel.z)
  const totalDelta = deltaX + deltaY + deltaZ

  lastAccel = { x: accel.x, y: accel.y, z: accel.z }

  // 摇动阈值: 总变化量 > 30, 防抖 1.5 秒
  const now = Date.now()
  if (totalDelta > 30 && now - lastShakeTime > 1500) {
    lastShakeTime = now
    throwCoins()
  }
}

async function initMotion() {
  if (!('DeviceMotionEvent' in window)) return

  // iOS 13+ 需要请求权限
  if (typeof DeviceMotionEvent.requestPermission === 'function') {
    try {
      const permission = await DeviceMotionEvent.requestPermission()
      if (permission !== 'granted') return
    } catch {
      return
    }
  }

  motionSupported.value = true
  window.addEventListener('devicemotion', handleMotion)
}

onMounted(() => {
  initMotion()
})

onUnmounted(() => {
  window.removeEventListener('devicemotion', handleMotion)
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ShakeDivination.vue
git commit -m "feat: add device motion shake detection with iOS permission handling"
```

---

### Task 5: Integrate ShakeDivination into YaoInput page

**Files:**
- Modify: `frontend/src/views/YaoInput.vue`

- [ ] **Step 1: Add mode toggle and ShakeDivination import**

Replace the entire `YaoInput.vue` content with the updated version that adds mode switching. The key changes are:
1. Add a `mode` ref and tab switcher UI
2. Wrap existing manual input in `v-if="mode === 'manual'"`
3. Add `<ShakeDivination>` in `v-else`
4. Handle the `@complete` event

Update the `<template>` section:

```html
<template>
  <div class="page yao-page">
    <div class="time-section card">
      <label class="time-label">{{ $t('摇卦时间') }}</label>
      <div class="time-pickers">
        <select v-model="selYear" class="time-sel">
          <option v-for="y in yearList" :key="y" :value="y">{{ y }}{{ $t('年') }}</option>
        </select>
        <select v-model="selMonth" class="time-sel">
          <option v-for="m in 12" :key="m" :value="m">{{ m }}{{ $t('月') }}</option>
        </select>
        <select v-model="selDay" class="time-sel">
          <option v-for="d in daysInMonth" :key="d" :value="d">{{ d }}{{ $t('日') }}</option>
        </select>
        <select v-model="selHour" class="time-sel">
          <option v-for="h in 24" :key="h-1" :value="h-1">{{ h-1 }}{{ $t('时') }}</option>
        </select>
        <select v-model="selMinute" class="time-sel">
          <option v-for="m in 60" :key="m-1" :value="m-1">{{ String(m-1).padStart(2,'0') }}{{ $t('分') }}</option>
        </select>
      </div>
    </div>

    <!-- 模式切换 -->
    <div class="mode-tabs">
      <button
        class="mode-tab"
        :class="{ active: mode === 'manual' }"
        @click="mode = 'manual'"
      >{{ $t('手动输入') }}</button>
      <button
        class="mode-tab"
        :class="{ active: mode === 'shake' }"
        @click="mode = 'shake'"
      >{{ $t('摇动起卦') }}</button>
    </div>

    <!-- 手动输入模式 -->
    <template v-if="mode === 'manual'">
      <div class="yao-section">
        <div class="yao-row" v-for="(row, index) in displayRows" :key="index">
          <span class="yao-label">{{ $t(row.label) }}</span>
          <div class="yao-buttons">
            <button
              v-for="opt in options"
              :key="opt.value"
              class="yao-btn"
              :class="{ selected: yaoValues[row.dataIndex] === opt.value }"
              @click="yaoValues[row.dataIndex] = opt.value"
            >{{ $t(opt.label) }}</button>
          </div>
        </div>
      </div>
      <button class="btn-primary" @click="submit">{{ $t('排盘') }}</button>
    </template>

    <!-- 摇动起卦模式 -->
    <ShakeDivination v-else @complete="onShakeComplete" />
  </div>
</template>
```

- [ ] **Step 2: Update script section**

Add to the `<script setup>`:

```javascript
import ShakeDivination from '../components/ShakeDivination.vue'

const mode = ref('manual')

function onShakeComplete(values) {
  // 与手动模式共用同一个 submit 逻辑
  const maxDay = daysInMonth.value
  const day = selDay.value > maxDay ? maxDay : selDay.value

  sessionStorage.setItem('liuyao_date', JSON.stringify({
    year: selYear.value,
    month: selMonth.value,
    day: day,
    hour: selHour.value
  }))
  sessionStorage.setItem('liuyao_yaoValues', JSON.stringify(values))
  router.push('/hexagram')
}
```

- [ ] **Step 3: Add mode-tabs CSS**

Add to `<style scoped>`:

```css
.mode-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border: 1px solid var(--color-border);
  border-radius: 1px;
  overflow: hidden;
}
.mode-tab {
  flex: 1;
  height: 40px;
  background: var(--color-card);
  color: var(--color-text-secondary);
  font-size: 15px;
  border: none;
  transition: all 0.2s ease;
}
.mode-tab.active {
  background: var(--color-primary);
  color: #141414;
  font-weight: 500;
}
```

- [ ] **Step 4: Verify the page renders without errors**

Run: `cd frontend && npx vite build 2>&1 | tail -5`
Expected: Build completes without errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/YaoInput.vue frontend/src/components/ShakeDivination.vue
git commit -m "feat: integrate shake divination mode into YaoInput with tab switching"
```

---

### Task 6: Polish animation and fix coin final-rotation

**Files:**
- Modify: `frontend/src/components/ShakeDivination.vue`

The CSS `@keyframes` uses `var(--final-rotation)` at 100% which won't work because CSS custom properties set via JS on `.coin` elements need the animation to reference them correctly. We need to switch from CSS animation to JS-driven animation classes.

- [ ] **Step 1: Refactor coin animation to use class-based final state**

Replace the coin animation approach: instead of `var(--final-rotation)` in keyframes, use a two-phase approach:
1. During animation: apply a spinning class with fixed keyframes
2. After animation ends: remove spinning class, apply final rotation via inline style

Update `throwCoins` function — replace the `nextTick` block and the setTimeout:

```javascript
function throwCoins() {
  if (phase.value !== 'idle' || allDone.value) return

  const results = [
    Math.random() < 0.5 ? '正' : '背',
    Math.random() < 0.5 ? '正' : '背',
    Math.random() < 0.5 ? '正' : '背',
  ]
  const backs = results.filter(c => c === '背').length

  coinResults[0] = results[0]
  coinResults[1] = results[1]
  coinResults[2] = results[2]
  currentYaoValue.value = backs

  // 开始动画
  phase.value = 'animating'
  isAnimating.value = true
  hasResult.value = false

  // 动画结束后显示最终结果
  setTimeout(() => {
    isAnimating.value = false
    hasResult.value = true
    phase.value = 'result'
  }, 1500)
}
```

Replace the `@keyframes coinFlip` and related CSS with:

```css
/* 翻转动画: 固定旋转圈数 */
.coin-flip {
  animation: coinSpin 1.2s ease-in-out forwards;
}
.coin-wrapper:nth-child(2) .coin-flip {
  animation-delay: 0.15s;
}
.coin-wrapper:nth-child(3) .coin-flip {
  animation-delay: 0.3s;
}

@keyframes coinSpin {
  0% { transform: rotateY(0deg) translateY(0); }
  20% { transform: rotateY(360deg) translateY(-50px); }
  40% { transform: rotateY(720deg) translateY(-60px); }
  60% { transform: rotateY(1080deg) translateY(-30px); }
  80% { transform: rotateY(1440deg) translateY(-10px); }
  100% { transform: rotateY(1800deg) translateY(0); }
}

/* 落定状态: 正面朝上 (1800deg = 偶数圈, 正面) */
.coin-heads {
  transform: rotateY(0deg);
}
/* 落定状态: 背面朝上 */
.coin-tails {
  transform: rotateY(180deg);
}
```

Note: 1800deg = 5 full rotations, ends at 0deg (showing front). Since `coinSpin` always ends at 1800deg (= 0deg equivalent), after animation we remove the class and apply `.coin-heads` or `.coin-tails` for the actual result. The transition from spin-end to final-state is seamless because heads is already at 0deg. For tails, the `transition: transform 0.3s` on `.coin` handles the final 180deg flip.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ShakeDivination.vue
git commit -m "fix: refactor coin animation to use reliable class-based final rotation"
```

---

### Task 7: Final integration test and cleanup

**Files:**
- Modify: `frontend/src/components/ShakeDivination.vue` (if needed)
- Modify: `frontend/src/views/YaoInput.vue` (if needed)

- [ ] **Step 1: Build frontend to verify no compilation errors**

Run: `cd frontend && npm run build`
Expected: Build succeeds, no errors.

- [ ] **Step 2: Manual smoke test checklist**

Start dev server (`cd frontend && npm run dev`) and test in browser:

1. Open `/yao-input` — verify mode tabs render ("手动输入" / "摇动起卦")
2. Default is "手动输入" — verify existing manual mode works unchanged
3. Click "摇动起卦" tab — verify shake UI renders (progress bar + coins + button)
4. Click "点击摇卦" — verify 3D coin flip animation plays
5. After animation — verify coins show 正/背 result and result text appears
6. Click "确认，下一爻" — verify progress bar updates, step advances
7. Repeat 6 times — verify result summary shows all 6 yao values
8. Click "开始排盘" — verify navigates to `/hexagram` with correct data
9. On `/hexagram` — verify hexagram calculation renders correctly
10. Switch back to "手动输入" tab — verify manual mode still works

- [ ] **Step 3: Fix any issues found during testing**

Address any visual or functional issues found in step 2.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete shake divination mode with 3D coin animation"
```
