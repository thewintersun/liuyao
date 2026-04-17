<template>
  <div class="page terms-page">
    <h2 class="page-title">{{ $t('用户协议与隐私政策') }}</h2>
    <div class="content">
      <p class="updated-at">{{ $t('最后更新：') }}2026-04-17</p>

      <h3>{{ $t('第一部分 · 用户协议') }}</h3>

      <h4>{{ $t('1. 服务性质与范围') }}</h4>
      <p>本应用提供基于中国传统六爻理论的占卜排盘服务，结合人工智能生成解卦分析，仅供娱乐、文化学习和个人参考之用，不构成任何专业建议。</p>

      <h4>{{ $t('2. 账号注册与安全') }}</h4>
      <p>您需提供真实有效的邮箱地址完成注册。账号由您本人使用，请妥善保管密码。因密码泄露导致的损失由用户自行承担。</p>

      <h4>{{ $t('3. 使用规范') }}</h4>
      <p>禁止通过自动化工具批量调用接口、爬取数据或实施任何可能影响服务稳定性的行为。禁止将本服务用于违法或违反公序良俗的目的。</p>

      <h4>{{ $t('4. 服务变更与终止') }}</h4>
      <p>本应用有权随时修改、暂停或终止全部或部分服务，无需事先通知。对于免费额度的调整，本应用保留最终解释权。</p>

      <h4>{{ $t('5. 免责限制') }}</h4>
      <p>六爻预测结果不保证准确性，不应作为医疗、法律、投资等重大决策依据。因使用本服务产生的任何损失，本应用不承担责任。</p>

      <h4>{{ $t('6. 适用法律与争议解决') }}</h4>
      <p>本协议适用中华人民共和国法律。如发生争议，双方应友好协商解决；协商不成的，提交本应用运营方所在地有管辖权的法院处理。</p>

      <h3>{{ $t('第二部分 · 隐私政策') }}</h3>

      <h4>{{ $t('1. 收集的信息') }}</h4>
      <p>我们收集以下信息：注册时的用户名和邮箱地址；使用服务时的 IP 地址、设备信息；您输入的起卦参数和与 AI 的对话内容；使用记录（时间、次数）。</p>

      <h4>{{ $t('2. 如何使用信息') }}</h4>
      <p>收集的信息用于：提供 AI 解卦服务；账户管理与身份验证；防范滥用和安全防护；改善服务质量（统计分析）。</p>

      <h4>{{ $t('3. 第三方共享') }}</h4>
      <p>您的对话内容（起卦参数、问题描述）将发送至大模型服务商的API进行AI处理，大模型服务商的隐私政策独立适用。除此之外，我们不向第三方出售或共享您的个人信息。</p>

      <h4>{{ $t('4. 数据存储与期限') }}</h4>
      <p>数据存储于服务器本地数据库。账户注销后，您的个人信息将在 30 天内删除。</p>

      <h4>{{ $t('5. 用户权利') }}</h4>
      <p>您有权查阅、更正或删除您的个人信息，包括申请注销账号。如需行使上述权利，请发送邮件至：<strong>thewintersun@gmail.com</strong>，我们将在 15 个工作日内处理。</p>

      
    </div>
  </div>
</template>

<style scoped>
.content {
  padding: 0 4px;
}
.updated-at {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin-bottom: 16px;
}
.content h3 {
  color: var(--color-primary);
  font-size: 18px;
  font-weight: bold;
  margin: 24px 0 8px;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 8px;
}
.content h4 {
  color: var(--color-primary);
  font-size: 15px;
  margin: 16px 0 6px;
}
.content p {
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.8;
  margin-bottom: 8px;
}
.content strong {
  color: var(--color-primary);
}
.template-notice {
  margin-top: 24px;
  padding: 12px;
  background: rgba(249, 212, 124, 0.08);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  color: var(--color-text-secondary);
  font-size: 13px;
}
</style>
