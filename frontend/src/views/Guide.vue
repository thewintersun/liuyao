<template>
  <div class="page guide-page">
    <div class="quote-box">
      <p class="quote-text">{{ $t('卦不敢算尽，畏世道无常。') }}</p>
      <p class="quote-text">{{ $t('福自己作，命自己求。') }}</p>
    </div>

    <h3 class="main-title">{{ $t('六爻起卦必读') }}</h3>

    <div class="section">
      <h4 class="section-title">{{ $t('1. 心诚则灵') }}</h4>
      <p class="section-text">{{ $t('保持专注、虔诚的心态，避免嬉戏或轻慢。') }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('2. 环境清净') }}</h4>
      <p class="section-text">{{ $t('选择安静、不受干扰的地方，避免在嘈杂或情绪波动时起卦。') }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('3. 意念集中') }}</h4>
      <p class="section-text">{{ $t('起卦之时，心中默念所求之事，这点对起卦的准确度很重要。') }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('4. 具体明确') }}</h4>
      <p class="section-text">{{ $t("心中默念所求之事，确保问题明确具体.（如'近期工作发展如何？';而不是模糊的'我未来怎样？'）。") }}</p>
      <p class="section-text">{{ $t("- 一事一求，默念所求之事要是一件具体的事。如：不能是'选择A还是选择B？'，应该是'选择A如何？'") }}</p>
      <p class="section-text">{{ $t('- 一卦仅针对一个问题，避免混杂多个事项。若需问其他问题，需重新起卦。') }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('5. 时间选择') }}</h4>
      <p class="section-text">{{ $t('传统认为子时（23:00-1:00）不宜起卦，因阴阳交接易混乱。') }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('6. 回避禁忌') }}</h4>
      <p class="section-text">{{ $t('饮酒后、情绪极端（如大怒、大悲）时不宜占卜；同一问题短期内不重复占（需待事态变化后再占）。') }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('7. 卦象验证') }}</h4>
      <p class="section-text">{{ $t('若卦象杂乱无章（如多爻乱动），可能因心不诚或问题不当，可暂停反思后重新占。') }}</p>
    </div>

    <div class="divider"></div>

    <h3 class="main-title">{{ $t('如何确定所求事宜类别') }}</h3>

    <div class="section">
      <h4 class="section-title">{{ $t('1. 明确问题类型') }}</h4>
      <p class="section-text">{{ $t('先问自己是问的什么事？比如是问工作、钱财、健康，还是感情？不同的事情对应不同的类别。') }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('2. 父母') }}</h4>
      <p class="section-text">{{ $t("代表：房子、车子、合同、学习、考试、长辈，信息，总之像'保护伞'一样的东西。") }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('3. 官鬼') }}</h4>
      <p class="section-text">{{ $t('代表：工作、升职、官司、疾病、鬼神，男朋友，老公， 总之管着你或让你害怕的东西。') }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('4. 兄弟') }}</h4>
      <p class="section-text">{{ $t("代表： 朋友、借钱、分财产、竞争对手，总之和你平起平坐的'竞争者'。") }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('5. 妻财') }}</h4>
      <p class="section-text">{{ $t("代表： 钱财、工资、投资、妻子，女朋友，总之属于你控制的'资源'。") }}</p>
    </div>
    <div class="section">
      <h4 class="section-title">{{ $t('6. 子孙') }}</h4>
      <p class="section-text">{{ $t('代表：孩子、娱乐、宠物、医药、求平安，总之让你快乐平安的事情。') }}</p>
    </div>
  </div>
</template>

<style scoped>
.quote-box {
  text-align: center;
  padding: 20px;
  margin-bottom: 16px;
}
.quote-text {
  color: var(--color-primary);
  font-size: 18px;
  line-height: 2;
  font-style: italic;
}
.main-title {
  color: var(--color-primary);
  font-size: 20px;
  font-weight: 500;
  text-align: center;
  margin-bottom: 16px;
}
.section {
  margin-bottom: 16px;
}
.section-title {
  color: var(--color-primary);
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 6px;
}
.section-text {
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.8;
}
</style>
