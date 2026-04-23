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

    <ShakeDivination v-if="mode === 'shake'" :date-info="currentDateInfo" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import ShakeDivination from '../components/ShakeDivination.vue'

const router = useRouter()

const STORAGE_KEY = 'liuyao_yaoInput_state'

// 尝试恢复之前的状态
const saved = (() => {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
})()

// 模式切换: 'manual' | 'shake'
const mode = ref(saved?.mode || 'manual')

// 时间：优先恢复保存的值，否则用当前时间
const now = new Date()
const selYear = ref(saved?.year ?? now.getFullYear())
const selMonth = ref(saved?.month ?? (now.getMonth() + 1))
const selDay = ref(saved?.day ?? now.getDate())
const selHour = ref(saved?.hour ?? now.getHours())
const selMinute = ref(saved?.minute ?? now.getMinutes())

// 年份列表: 当前年份前后范围
const yearList = computed(() => {
  const curr = new Date().getFullYear()
  const list = []
  for (let y = curr - 100; y <= curr + 1; y++) list.push(y)
  return list
})

// 当月天数，自动适配闰年和月份
const daysInMonth = computed(() => {
  return new Date(selYear.value, selMonth.value, 0).getDate()
})

// 切换年/月时自动修正日期溢出
watch([selYear, selMonth], () => {
  const max = new Date(selYear.value, selMonth.value, 0).getDate()
  if (selDay.value > max) selDay.value = max
})

// 6个爻的值 (index 0=初爻/第一次摇, 5=上爻/第六次摇), 默认全部一背(1)
const yaoValues = reactive(saved?.yaoValues || [1, 1, 1, 1, 1, 1])

// 保存表单状态到 sessionStorage
function saveState() {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
    mode: mode.value,
    year: selYear.value,
    month: selMonth.value,
    day: selDay.value,
    hour: selHour.value,
    minute: selMinute.value,
    yaoValues: [...yaoValues]
  }))
}

watch([mode, selYear, selMonth, selDay, selHour, selMinute], saveState)
watch(yaoValues, saveState)

const options = [
  { label: '一背', value: 1 },
  { label: '二背', value: 2 },
  { label: '三背', value: 3 },
  { label: '无背', value: 0 },
]

// 显示顺序: 从上到下显示第六次→第一次 (对应数组索引 5→0)
const displayRows = [
  { label: '第六次摇', dataIndex: 5 },
  { label: '第五次摇', dataIndex: 4 },
  { label: '第四次摇', dataIndex: 3 },
  { label: '第三次摇', dataIndex: 2 },
  { label: '第二次摇', dataIndex: 1 },
  { label: '第一次摇', dataIndex: 0 },
]

function submit() {
  // 修正日期溢出 (比如从31号月份切到30天月份)
  const maxDay = daysInMonth.value
  const day = selDay.value > maxDay ? maxDay : selDay.value

  sessionStorage.removeItem('liuyao_currentRecordId')
  sessionStorage.setItem('liuyao_date', JSON.stringify({
    year: selYear.value,
    month: selMonth.value,
    day: day,
    hour: selHour.value
  }))
  sessionStorage.setItem('liuyao_yaoValues', JSON.stringify([...yaoValues]))
  router.push('/hexagram')
}

// 当前日期信息（传给 ShakeDivination 用于直接导航）
const currentDateInfo = computed(() => {
  const maxDay = daysInMonth.value
  return {
    year: selYear.value,
    month: selMonth.value,
    day: selDay.value > maxDay ? maxDay : selDay.value,
    hour: selHour.value
  }
})
</script>

<style scoped>
.time-section {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.time-label {
  color: var(--color-primary);
  font-size: 16px;
  white-space: nowrap;
}
.time-pickers {
  display: flex;
  gap: 8px;
}
.time-sel {
  flex: 1;
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  padding: 8px 4px;
  font-size: 15px;
  font-family: inherit;
  appearance: auto;
}
.yao-section {
  margin-bottom: 16px;
}
.yao-row {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(249,212,124,0.2);
}
.yao-label {
  color: var(--color-primary);
  font-size: 15px;
  width: 80px;
  flex-shrink: 0;
}
.yao-buttons {
  display: flex;
  gap: 8px;
  flex: 1;
}
.yao-btn {
  flex: 1;
  height: 36px;
  background: var(--color-card);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  font-size: 14px;
}
.yao-btn.selected {
  background: #FFFFFF;
  color: #141414;
  border-color: #FFFFFF;
}
.mode-tabs {
  display: flex;
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
</style>
