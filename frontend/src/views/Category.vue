<template>
  <div class="page category-page">
    <div class="category-header">
      <span class="header-col-title">{{ $t('类别') }}</span>
      <span class="header-col-desc">{{ $t('所问之事') }}</span>
    </div>

    <div class="category-list">
      <div
        v-for="(cat, index) in categories"
        :key="index"
        class="category-item touchable"
        :class="{ selected: selectedIndex === index }"
        @click="selectedIndex = index"
      >
        <span class="cat-title">{{ $t(cat.title) }}</span>
        <span class="cat-desc">{{ $t(cat.desc) }}</span>
      </div>
    </div>

    <div class="hint-text">{{ $t('详细说明请参考：设置->起卦必读') }}</div>

    <button class="btn-primary" @click="confirm">{{ $t('确定') }}</button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { t } from '../utils/locale.js'
import { showToast } from '../utils/toast.js'

const router = useRouter()
// 不预选：用神完全由这里决定，选错会让整卦分析取错爻，
// 预设一个默认值会让相当一部分人不看说明直接提交。
const selectedIndex = ref(-1)

// 描述按「你要问什么就选它」来写，而不是罗列六亲的抽象含义——
// 用神完全由这里的选择决定，选错会让整卦分析取错爻。
// 兄弟与自占自身两条带反向提示，拦住最常见的误选。
const categories = [
  { title: '父母', desc: '父母长辈、房屋、车辆、合同文书、证书、考试学业、搬迁' },
  { title: '官鬼', desc: '工作职位、求职、升职、考核、官司、领导上司；女占男友或丈夫；疾病的病情' },
  { title: '兄弟', desc: '兄弟姐妹、朋友同事、合作伙伴本人如何。注意：问自己能否赚到钱请选「妻财」，不要选这里' },
  { title: '妻财', desc: '求财必选：赚钱、收入、工资、投资、生意、创业收益、买卖、要账；男占女友或妻子' },
  { title: '子孙', desc: '子女晚辈、学生、宠物；求平安、消灾解忧；看病能否治好、用药是否对症' },
  { title: '自占自身', desc: '单纯问自己近期整体状态、运势走向。若已明确问某件事（钱、工作、感情、健康），请选其他类别' },
]

function confirm() {
  if (selectedIndex.value < 0) {
    showToast(t('请先选择所问之事的类别'), 'warning')
    return
  }
  sessionStorage.setItem('liuyao_category', JSON.stringify({
    title: categories[selectedIndex.value].title,
    index: selectedIndex.value
  }))
  router.push('/analysis')
}
</script>

<style scoped>
.category-header {
  display: flex;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 4px;
}
.header-col-title {
  width: 80px;
  color: var(--color-primary);
  font-size: 16px;
  font-weight: 500;
}
.header-col-desc {
  flex: 1;
  color: var(--color-primary);
  font-size: 16px;
  font-weight: 500;
}
.category-list {
  margin-bottom: 12px;
}
.category-item {
  display: flex;
  padding: 14px 0;
  border-bottom: 1px solid rgba(249,212,124,0.15);
  cursor: pointer;
}
.category-item.selected {
  background: rgba(249,212,124,0.2);
  border-left: 3px solid var(--color-primary);
  padding-left: 10px;
}
.cat-title {
  width: 80px;
  color: var(--color-primary);
  font-size: 15px;
  flex-shrink: 0;
}
.cat-desc {
  flex: 1;
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.5;
}
.hint-text {
  color: var(--color-text-secondary);
  font-size: 12px;
  text-align: center;
  margin-bottom: 16px;
}
</style>
