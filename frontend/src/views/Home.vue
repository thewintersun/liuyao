<template>
  <div class="page home-page">
    <h2 class="page-title">{{ $t('六爻起卦须知') }}</h2>
    <div class="divider"></div>
    <div class="home-content">
      <div class="section">
        <h3 class="section-title">{{ $t('原则') }}</h3>
        <p class="section-text">{{ $t('一事一问，心诚则灵，戏卦不验，子时(23:00-1:00)不占。') }}</p>
      </div>
      <div class="section">
        <h3 class="section-title">{{ $t('准备') }}</h3>
        <p class="section-text">{{ $t('在安静房间内坐定、避免无关干扰，净手、静心，准备好纸笔及3枚相同硬币(同材质同大小同面值)。') }}</p>
      </div>
      <div class="section">
        <h3 class="section-title">{{ $t('摇卦') }}</h3>
        <p class="section-text">{{ $t('将3枚硬币合扣于手心，集中精神默想所问之事，充分摇动后自然落于硬质平面(软床等不可)，记录硬币的背面的个数，连续摇动6次;摇卦务必一次性完成，若中断，此卦作废。') }}</p>
      </div>
      <div class="section">
        <h3 class="section-title">{{ $t('记录格式') }}</h3>
        <p class="section-text" v-html="$t('20XX年X月X日X点X分') + '<br/>' + $t('1. 几背 2. 几背 3. 几背 4. 几背 5. 几背 6. 几背')"></p>
      </div>
    </div>
    <button class="btn-primary home-btn" @click="$router.push('/yao-input')">{{ $t('开始起卦') }}</button>
  </div>
</template>

<script setup>
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 56px);
}
.home-content {
  flex: 1;
}
.section {
  margin-bottom: 20px;
}
.section-title {
  color: var(--color-primary);
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 8px;
}
.section-text {
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.8;
}
.home-btn {
  margin-top: 20px;
}
</style>
