<template>
  <div ref="cardRef" :style="cardStyle">
    <!-- 标题 -->
    <div :style="titleStyle">✦ 六爻解卦 ✦</div>

    <!-- 时间信息 -->
    <div :style="infoStyle">
      <div :style="infoRowStyle">时间: {{ guaXiangInfo.time?.[0] || '' }}</div>
      <div :style="infoRowStyle">干支: {{ guaXiangInfo.timecn?.[0] || '' }}</div>
      <div :style="infoRowStyle">旬空: {{ guaXiangInfo.kongwang?.[0] || '' }}</div>
    </div>

    <!-- 主变卦名 -->
    <div :style="guaNamesStyle">
      {{ mainGuaGongText }} → {{ bianGuaGongText }}
    </div>

    <!-- 排盘表格 -->
    <div :style="tableStyle">
      <!-- 表头 -->
      <div :style="tableRowStyle">
        <div :style="colLiushenHeaderStyle">六神</div>
        <div :style="colFushenHeaderStyle">伏神</div>
        <div :style="colBenguaHeaderStyle">本 卦</div>
        <div :style="colBianguaHeaderStyle">变 卦</div>
      </div>
      <!-- 6行：从上爻到初爻 -->
      <div v-for="r in 6" :key="r" :style="tableRowStyle">
        <div :style="colLiushenStyle">{{ getLiushen(r - 1) }}</div>
        <div :style="colFushenStyle">{{ getFushen(r - 1) }}</div>
        <div :style="colBenguaStyle">
          <span>{{ getMainLiuqin(r - 1) }}</span>
          <span v-if="hasYaoData">{{ getYaoSymbol(r - 1, 'main') }}</span>
          <span v-if="isDyao(r - 1)" :style="dyaoMarkStyle">{{ getDyaoMark(r - 1) }}</span>
          <span v-if="isShiYao(r - 1)" :style="shiYingStyle">世</span>
          <span v-if="isYingYao(r - 1)" :style="shiYingStyle">应</span>
        </div>
        <div :style="colBianguaStyle">
          <span>{{ getBianLiuqin(r - 1) }}</span>
          <span v-if="hasYaoData">{{ getYaoSymbol(r - 1, 'bian') }}</span>
        </div>
      </div>
      <!-- 底行信息 -->
      <div :style="tableRowStyle">
        <div :style="colLiushenStyle"></div>
        <div :style="colFushenStyle"></div>
        <div :style="colBenguaFooterStyle">{{ mainGuaFooter }}</div>
        <div :style="colBianguaFooterStyle">{{ bianGuaFooter }}</div>
      </div>
    </div>

    <!-- 分隔线 + 解卦标题 -->
    <div :style="dividerStyle">── 解卦 ──────────────</div>

    <!-- AI 解卦内容 -->
    <div :style="contentStyle">{{ cleanMessage }}</div>

    <!-- 底部水印 -->
    <div :style="watermarkDividerStyle"></div>
    <div :style="watermarkStyle">🔮 AI智能解卦 liuyao666.top</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  guaXiangInfo: { type: Object, required: true },
  message: { type: String, default: '' }
})

const hasYaoData = computed(() => {
  return props.guaXiangInfo.maingua_yao && props.guaXiangInfo.maingua_yao.length === 6
})

const mainGuaGongText = computed(() => {
  const g = props.guaXiangInfo.maingua_gong
  return g ? `${g[0]}: ${g[1]}` : ''
})

const bianGuaGongText = computed(() => {
  const g = props.guaXiangInfo.biangua_gong
  return g ? `${g[0]}: ${g[1]}` : ''
})

const mainGuaFooter = computed(() => {
  const parts = []
  if (props.guaXiangInfo.maingua_liuchong?.[0]) parts.push(props.guaXiangInfo.maingua_liuchong[0])
  if (props.guaXiangInfo.maingua_youhun?.[0]) parts.push(props.guaXiangInfo.maingua_youhun[0])
  return parts.join(' ')
})

const bianGuaFooter = computed(() => {
  const parts = []
  if (props.guaXiangInfo.biangua_liuchong?.[0]) parts.push(props.guaXiangInfo.biangua_liuchong[0])
  if (props.guaXiangInfo.biangua_youhun?.[0]) parts.push(props.guaXiangInfo.biangua_youhun[0])
  return parts.join(' ')
})

// 清理 Markdown 标记为纯文本，并截掉最后一个 --- 之后的结尾引导语
const cleanMessage = computed(() => {
  if (!props.message) return ''
  let text = props.message
  // 截掉最后一个 --- 分隔线及其后的内容（通常是"欢迎继续追问"之类的引导语）
  const lastSep = text.lastIndexOf('---')
  if (lastSep > 0) {
    text = text.substring(0, lastSep)
  }
  return text
    .replace(/#{1,6}\s*/g, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/`(.*?)`/g, '$1')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/^[-*+]\s/gm, '• ')
    .replace(/^\d+\.\s/gm, (m) => m)
    .trim()
})

// row: 0-5, 0=上爻, 5=初爻
// guaXiangInfo中 liuqin/fushen: 0=上爻; liushen/yao: 0=初爻
function getLiushen(row) {
  const arr = props.guaXiangInfo.liushen
  return arr ? (arr[5 - row] || '') : ''
}

function getFushen(row) {
  const arr = props.guaXiangInfo.fugua_liuqin
  return arr ? (arr[row] || '') : ''
}

function getMainLiuqin(row) {
  const arr = props.guaXiangInfo.maingua_liuqin
  return arr ? (arr[row] || '') : ''
}

function getBianLiuqin(row) {
  const arr = props.guaXiangInfo.biangua_liuqin
  return arr ? (arr[row] || '') : ''
}

function getYaoSymbol(row, type) {
  const arr = type === 'main' ? props.guaXiangInfo.maingua_yao : props.guaXiangInfo.biangua_yao
  if (!arr) return ''
  const val = arr[5 - row]
  return val === '1' ? '▅▅▅▅▅' : '▅▅　▅▅'
}

function isDyao(row) {
  const dyao = props.guaXiangInfo.dyao_display
  if (!dyao) return false
  const pos = String(5 - row)
  return dyao.some(d => d.split(' ')[0] === pos)
}

function getDyaoMark(row) {
  const dyao = props.guaXiangInfo.dyao_display
  if (!dyao) return ''
  const pos = String(5 - row)
  const found = dyao.find(d => d.split(' ')[0] === pos)
  return found ? found.split(' ')[1] : ''
}

function isShiYao(row) {
  const shi = props.guaXiangInfo.shiyao_weizhi
  if (!shi) return false
  return (5 - row) === parseInt(shi[0])
}

function isYingYao(row) {
  const ying = props.guaXiangInfo.yingyao_weizhi
  if (!ying) return false
  return (5 - row) === parseInt(ying[0])
}

// ===== 内联样式 =====
const cardStyle = {
  width: '400px',
  backgroundColor: '#141414',
  padding: '20px',
  fontFamily: '"楷体", "KaiTi", "STKaiti", serif',
  color: '#D9D9D9',
  boxSizing: 'border-box'
}

const titleStyle = {
  textAlign: 'center',
  fontSize: '20px',
  fontWeight: 'bold',
  color: '#F9D47C',
  padding: '8px 0 12px',
  letterSpacing: '2px'
}

const infoStyle = {
  padding: '0 0 8px'
}

const infoRowStyle = {
  fontSize: '13px',
  color: '#D9D9D9',
  lineHeight: '1.8'
}

const guaNamesStyle = {
  textAlign: 'center',
  fontSize: '15px',
  color: '#F9D47C',
  padding: '8px 0'
}

const tableStyle = {
  border: '1px solid rgba(249,212,124,0.3)',
  margin: '4px 0 12px'
}

const tableRowStyle = {
  display: 'flex',
  borderBottom: '1px solid rgba(249,212,124,0.15)',
  minHeight: '32px',
  alignItems: 'center'
}

const colHeaderBase = {
  textAlign: 'center',
  padding: '6px 2px',
  color: '#F9D47C',
  fontSize: '12px',
  fontWeight: 'bold'
}

const colLiushenHeaderStyle = { ...colHeaderBase, width: '11%', flexShrink: 0 }
const colFushenHeaderStyle = { ...colHeaderBase, width: '15%', flexShrink: 0 }
const colBenguaHeaderStyle = { ...colHeaderBase, width: '40%', flexShrink: 0 }
const colBianguaHeaderStyle = { ...colHeaderBase, width: '34%', flexShrink: 0 }

const colCellBase = {
  textAlign: 'center',
  padding: '4px 2px',
  fontSize: '12px'
}

const colLiushenStyle = { ...colCellBase, width: '11%', flexShrink: 0, color: '#999' }
const colFushenStyle = { ...colCellBase, width: '15%', flexShrink: 0, color: '#999', fontSize: '11px' }
const colBenguaStyle = {
  ...colCellBase,
  width: '40%',
  flexShrink: 0,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '2px',
  color: '#D9D9D9'
}
const colBianguaStyle = {
  ...colCellBase,
  width: '34%',
  flexShrink: 0,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '2px',
  color: '#D9D9D9'
}

const colBenguaFooterStyle = { ...colCellBase, width: '40%', flexShrink: 0, color: '#999', fontSize: '11px' }
const colBianguaFooterStyle = { ...colCellBase, width: '34%', flexShrink: 0, color: '#999', fontSize: '11px' }

const dyaoMarkStyle = { color: '#ff4d4f', fontWeight: 'bold', fontSize: '13px' }
const shiYingStyle = { color: '#F9D47C', fontWeight: 'bold', fontSize: '12px' }

const dividerStyle = {
  textAlign: 'center',
  color: '#F9D47C',
  fontSize: '13px',
  padding: '8px 0',
  letterSpacing: '1px'
}

const contentStyle = {
  fontSize: '13px',
  lineHeight: '1.8',
  color: '#D9D9D9',
  whiteSpace: 'pre-wrap',
  wordBreak: 'break-word',
  padding: '4px 0 12px'
}

const watermarkDividerStyle = {
  borderTop: '1px solid rgba(249,212,124,0.3)',
  margin: '0 0 8px'
}

const watermarkStyle = {
  textAlign: 'center',
  fontSize: '13px',
  color: '#F9D47C',
  padding: '4px 0',
  letterSpacing: '1px'
}
</script>
