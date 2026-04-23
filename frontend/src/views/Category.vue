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

const router = useRouter()
const selectedIndex = ref(5) // default: 自占自身

const categories = [
  { title: '父母', desc: '长辈、房子、车子、合同、学习、考试、建筑、公司等' },
  { title: '官鬼', desc: '工作、升职、官司、男朋友，老公、疾病、领导、恶人、烦恼等' },
  { title: '兄弟', desc: '兄弟、平辈、同事，竞争对手、分财产、合伙人、朋友等' },
  { title: '妻财', desc: '钱财、收入、女朋友、老婆、财务、工资、投资、物资等' },
  { title: '子孙', desc: '孩子、晚辈、自己的学生、宠物、医药、药品、娱乐、求平安等' },
  { title: '自占自身', desc: '自己摇卦占自身，如：自己问自己身体状况等' },
]

function confirm() {
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
