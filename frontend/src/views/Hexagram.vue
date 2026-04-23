<template>
  <div class="page hexagram-page">
    <!-- 时间信息 -->
    <div class="info-row">
      <span class="info-label">{{ $t('时间') }}</span>
      <span class="info-value">{{ timeStr }}</span>
    </div>
    <div class="info-row">
      <span class="info-label">{{ $t('干支') }}</span>
      <span class="info-value">{{ timeCn }}　{{ $t('旬空') }}: {{ kongwang }}</span>
    </div>
    <div class="divider"></div>

    <!-- 主变卦名 -->
    <div class="gua-names">
      <span>{{ mainGuaGong[0] }}: {{ mainGuaGong[1] }}</span>
      <span class="arrow">→</span>
      <span>{{ bianGuaGong[0] }}: {{ bianGuaGong[1] }}</span>
    </div>

    <!-- 四列排盘表格 -->
    <div class="paipan-table">
      <!-- 表头 -->
      <div class="table-header">
        <div class="col-liushen">{{ $t('六神') }}</div>
        <div class="col-fushen">{{ $t('伏神') }}</div>
        <div class="col-bengua">{{ $t('本卦') }}</div>
        <div class="col-biangua">{{ $t('变卦') }}</div>
      </div>

      <!-- 6行 从上爻(5)到初爻(0) -->
      <div class="table-row" v-for="i in 6" :key="i">
        <div class="col-liushen">{{ liushen[6 - i] }}</div>
        <div class="col-fushen fushen-text">{{ fushenDisplay[6 - i] }}</div>
        <div class="col-bengua">
          <span class="liuqin-text">{{ mainLiuqin[6 - i] }}</span>
          <span class="yao-symbol">{{ guaSymbol(gua[6 - i]) }}</span>
          <span v-if="isDyao(6 - i)" class="dyao-mark">{{ dyaoMark(6 - i) }}</span>
          <span v-if="isShiYao(6 - i)" class="shi-ying-mark">{{ $t('世') }}</span>
          <span v-if="isYingYao(6 - i)" class="shi-ying-mark">{{ $t('应') }}</span>
        </div>
        <div class="col-biangua">
          <span class="liuqin-text">{{ bianLiuqin[6 - i] }}</span>
          <span class="yao-symbol">{{ guaSymbol(bbgua[6 - i]) }}</span>
        </div>
      </div>

      <!-- 底行信息 -->
      <div class="table-footer">
        <div class="col-liushen"></div>
        <div class="col-fushen"></div>
        <div class="col-bengua footer-text">{{ mainGuaFooter }}</div>
        <div class="col-biangua footer-text">{{ bianGuaFooter }}</div>
      </div>
    </div>

    <!-- 底部按钮 -->
    <div class="bottom-buttons">
      <button class="btn-save" @click="saveHexagram">{{ $t('保存排盘') }}</button>
      <button class="btn-analysis" @click="goAnalysis">{{ $t('解卦') }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Liuyao } from '../core/liuyao.js'
import { saveRecord } from '../store/records.js'
import { t } from '../utils/locale.js'
import { showToast } from '../utils/toast.js'

const router = useRouter()
const ly = new Liuyao()

const timeStr = ref('')
const timeCn = ref('')
const kongwang = ref('')
const mainGuaGong = ref(['', ''])
const bianGuaGong = ref(['', ''])
const mainLiuqin = ref([])
const bianLiuqin = ref([])
const fushenData = ref([])
const liushen = ref([])
const gua = ref([])
const bbgua = ref([])
const dguaData = ref([])
const shiYao = ref(0)
const yingYao = ref(0)
const mainLiuchong = ref('')
const mainYouhun = ref('')
const bianLiuchong = ref('')
const bianYouhun = ref('')

let dateInfo = null
let yaoValues = null

onMounted(() => {
  const dateStr = sessionStorage.getItem('liuyao_date')
  const yaoStr = sessionStorage.getItem('liuyao_yaoValues')
  if (!dateStr || !yaoStr) {
    router.push('/yao-input')
    return
  }

  dateInfo = JSON.parse(dateStr)
  yaoValues = JSON.parse(yaoStr)

  ly.reset()
  ly.setDate(dateInfo.year, dateInfo.month, dateInfo.day, dateInfo.hour)
  ly.paipan(yaoValues)

  timeStr.value = ly.getTime()
  timeCn.value = ly.getTimeCn()
  kongwang.value = ly.getKongWangDisplay()
  mainGuaGong.value = ly.getGuaGong()
  bianGuaGong.value = ly.getBianGuaGong()
  // gua64数据存储顺序: index 0=上爻, index 5=初爻
  // 显示时需要反转为: index 0=初爻, index 5=上爻 (与gua/liushen数组一致)
  mainLiuqin.value = ly.getMainGuaLiuqin().reverse()
  bianLiuqin.value = ly.getBianGuaLiuqin().reverse()
  fushenData.value = ly.getFuShen().reverse()
  liushen.value = ly.getLiuShenList()
  gua.value = [...ly.gua]
  bbgua.value = [...ly.bbgua]
  dguaData.value = [...ly.dgua]
  shiYao.value = ly.getShiYaoWeizhi()
  yingYao.value = ly.getYingYaoWeizhi()
  mainLiuchong.value = ly.getLiuHeLiuChong()
  mainYouhun.value = ly.getYouHunGuiHun()
  bianLiuchong.value = ly.getBianGuaLiuHeLiuChong()
  bianYouhun.value = ly.getBianGuaYouHunGuiHun()

  // 存储 guaXiangInfo 到 sessionStorage 供后续 AI 解卦使用
  sessionStorage.setItem('liuyao_guaXiangInfo', JSON.stringify(ly.getGuaXiangInfo()))
})

const fushenDisplay = computed(() => {
  return fushenData.value
})

const mainGuaFooter = computed(() => {
  let s = ''
  if (mainLiuchong.value) s += mainLiuchong.value
  if (mainYouhun.value) s += (s ? ' ' : '') + mainYouhun.value
  return s
})

const bianGuaFooter = computed(() => {
  let s = ''
  if (bianLiuchong.value) s += bianLiuchong.value
  if (bianYouhun.value) s += (s ? ' ' : '') + bianYouhun.value
  return s
})

function guaSymbol(yaoVal) {
  return yaoVal === '1' ? '▅▅▅▅▅' : '▅▅　▅▅'
}

function isDyao(index) {
  for (let i = 0; i < dguaData.value.length; i += 2) {
    if (parseInt(dguaData.value[i]) === index) return true
  }
  return false
}

function dyaoMark(index) {
  for (let i = 0; i < dguaData.value.length; i += 2) {
    if (parseInt(dguaData.value[i]) === index) {
      return dguaData.value[i + 1] === '1' ? 'O' : 'X'
    }
  }
  return ''
}

function isShiYao(index) { return index === shiYao.value }
function isYingYao(index) { return index === yingYao.value }

async function saveHexagram() {
  const title = prompt(t('填写要保存卦例的名称'), timeStr.value)
  if (title !== null && title.trim()) {
    const date = new Date(dateInfo.year, dateInfo.month - 1, dateInfo.day, dateInfo.hour)
    const record = await saveRecord(title.trim(), date, yaoValues)
    sessionStorage.setItem('liuyao_currentRecordId', record.id)
    showToast(t('卦例已保存'), 'success')
  }
}

function goAnalysis() {
  router.push('/category')
}
</script>

<style scoped>
.info-row {
  display: flex;
  align-items: center;
  padding: 4px 0;
}
.info-label {
  color: var(--color-primary);
  font-size: 15px;
  width: 40px;
  flex-shrink: 0;
}
.info-value {
  color: var(--color-text);
  font-size: 14px;
}
.gua-names {
  text-align: center;
  color: var(--color-primary);
  font-size: 16px;
  padding: 8px 0;
}
.arrow {
  margin: 0 8px;
  color: var(--color-text-secondary);
}
.paipan-table {
  border: 1px solid var(--color-border);
  margin: 8px 0;
}
.table-header {
  display: flex;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-card);
}
.table-header > div {
  text-align: center;
  padding: 6px 2px;
  color: var(--color-primary);
  font-size: 13px;
}
.table-row {
  display: flex;
  border-bottom: 1px solid rgba(249,212,124,0.15);
  min-height: 38px;
  align-items: center;
}
.table-row > div {
  padding: 4px 2px;
  font-size: 13px;
  text-align: center;
}
.col-liushen { width: 11%; flex-shrink: 0; color: var(--color-text-secondary); }
.col-fushen { width: 15%; flex-shrink: 0; }
.col-bengua { width: 40%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; gap: 2px; flex-wrap: wrap; }
.col-biangua { width: 34%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; gap: 2px; flex-wrap: wrap; }
.fushen-text { color: var(--color-text-secondary); font-size: 12px; }
.liuqin-text { color: var(--color-text); font-size: 12px; white-space: nowrap; }
.yao-symbol { color: var(--color-text); font-size: 12px; letter-spacing: -1px; }
.dyao-mark { color: var(--color-danger); font-weight: bold; font-size: 13px; }
.shi-ying-mark { color: var(--color-primary); font-weight: bold; font-size: 12px; }
.table-footer {
  display: flex;
  min-height: 28px;
  align-items: center;
}
.table-footer > div {
  padding: 4px 2px;
  font-size: 12px;
  text-align: center;
}
.footer-text { color: var(--color-text-secondary); }
.bottom-buttons {
  display: flex;
  gap: 4%;
  margin-top: 16px;
}
.btn-save, .btn-analysis {
  flex: 1;
  height: 46px;
  font-size: 16px;
  border-radius: 1px;
  border: none;
}
.btn-save {
  background: var(--color-card);
  color: var(--color-primary);
  border: 1px solid var(--color-border);
}
.btn-analysis {
  background: var(--color-primary);
  color: #141414;
}
</style>
