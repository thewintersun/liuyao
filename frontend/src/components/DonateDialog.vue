<template>
  <div class="donate-overlay" v-if="visible" @click.self="close">
    <div class="donate-dialog">
      <p class="donate-title">{{ $t('请我喝杯咖啡') }}</p>
      <p class="donate-desc">{{ $t('本站免费使用，捐助完全自愿，不增加解卦额度。') }}</p>

      <!-- ===== 主路径：微信内置浏览器 → 微信码 ===== -->
      <template v-if="env === 'wechat'">
        <div class="qr-block" v-if="cfg.wechatQr">
          <img class="qr-img" :src="cfg.wechatQr" :alt="$t('微信收款码')" />
          <p class="qr-tip">{{ $t('长按上方图片，识别二维码') }}</p>
        </div>
        <div class="secondary" v-if="cfg.alipayUrl">
          <p class="secondary-label">{{ $t('习惯用支付宝？') }}</p>
          <button class="btn-ghost" @click="copyAlipayLink">
            {{ $t('复制链接，在浏览器中打开') }}
          </button>
        </div>
      </template>

      <!-- ===== 主路径：手机浏览器 / 支付宝内 → 跳转支付宝 ===== -->
      <template v-else-if="env === 'mobile'">
        <button class="btn-primary" v-if="cfg.alipayUrl" @click="openAlipay">
          {{ $t('用支付宝捐助') }}
        </button>
        <p class="fallback-tip" v-if="showAlipayFallback">
          {{ $t('没有反应？') }}
          <span class="link" @click="expandWechat = true">{{ $t('改用微信扫码') }}</span>
        </p>

        <div class="secondary" v-if="cfg.wechatQr">
          <p class="secondary-label link" v-if="!expandWechat" @click="expandWechat = true">
            {{ $t('习惯用微信？') }}
          </p>
          <div class="qr-block" v-else>
            <img class="qr-img" :src="cfg.wechatQr" :alt="$t('微信收款码')" />
            <p class="qr-tip">{{ $t('长按保存图片，再用微信「扫一扫」从相册选取') }}</p>
          </div>
        </div>
      </template>

      <!-- ===== 桌面端：两码并排 ===== -->
      <template v-else>
        <div class="qr-row">
          <div class="qr-block" v-if="cfg.wechatQr">
            <img class="qr-img" :src="cfg.wechatQr" :alt="$t('微信收款码')" />
            <p class="qr-tip">{{ $t('微信扫码') }}</p>
          </div>
          <div class="qr-block" v-if="cfg.alipayQr">
            <img class="qr-img" :src="cfg.alipayQr" :alt="$t('支付宝收款码')" />
            <p class="qr-tip">{{ $t('支付宝扫码') }}</p>
          </div>
        </div>
      </template>

      <p class="donate-thanks">{{ $t('无论是否捐助，功能完全一致。谢谢你的使用。') }}</p>
      <p class="donate-close" @click="close">{{ $t('关闭') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { DONATE_CONFIG } from '../config/donate.js'
import { showToast } from '../utils/toast.js'
import { t } from '../utils/locale.js'

const props = defineProps({
  visible: { type: Boolean, default: false }
})
const emit = defineEmits(['close'])

const cfg = DONATE_CONFIG
const expandWechat = ref(false)
const showAlipayFallback = ref(false)

/**
 * 环境判断：
 * - wechat：微信内置浏览器（排除企业微信），只能长按识别二维码，且微信会拦截支付宝域名
 * - mobile：手机浏览器 / 支付宝内置浏览器，可直接唤起支付宝
 * - desktop：桌面端，唤不起 App，只能扫码
 */
function detectEnv() {
  const ua = (navigator.userAgent || '').toLowerCase()
  if (/micromessenger/.test(ua) && !/wxwork/.test(ua)) return 'wechat'
  if (/alipayclient/.test(ua)) return 'mobile'
  if (/android|iphone|ipod|ipad/.test(ua)) return 'mobile'
  return 'desktop'
}

const env = ref(detectEnv())

// 每次打开弹窗重置次路径展开状态
watch(() => props.visible, (val) => {
  if (val) {
    expandWechat.value = false
    showAlipayFallback.value = false
  }
})

function close() {
  emit('close')
}

function openAlipay() {
  if (!cfg.alipayUrl) return
  // 未安装支付宝时跳转不会有反应，3 秒后页面仍可见则提示降级方案
  showAlipayFallback.value = false
  const timer = setTimeout(() => {
    if (document.visibilityState === 'visible') {
      showAlipayFallback.value = true
    }
  }, 3000)
  document.addEventListener('visibilitychange', () => clearTimeout(timer), { once: true })
  window.location.href = cfg.alipayUrl
}

function copyAlipayLink() {
  copyText(cfg.alipayUrl)
}

function copyText(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text)
      .then(() => showToast(t('已复制，请在浏览器中打开'), 'success'))
      .catch(() => fallbackCopy(text))
  } else {
    fallbackCopy(text)
  }
}

function fallbackCopy(text) {
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.position = 'fixed'
  ta.style.opacity = '0'
  document.body.appendChild(ta)
  ta.select()
  try {
    document.execCommand('copy')
    showToast(t('已复制，请在浏览器中打开'), 'success')
  } catch (e) {
    showToast(t('复制失败，请手动复制'), 'error')
  }
  document.body.removeChild(ta)
}
</script>

<style scoped>
.donate-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  padding: 20px;
}
.donate-dialog {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  max-width: 340px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}
.donate-title {
  color: var(--color-primary);
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 8px;
}
.donate-desc {
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 20px;
}
.qr-row {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
}
.qr-block {
  margin-bottom: 12px;
}
/* 必须是 img 标签且不加遮罩/圆角，否则微信无法长按识别 */
.qr-img {
  display: block;
  width: 200px;
  max-width: 100%;
  height: auto;
  margin: 0 auto;
  background: #FFFFFF;
  padding: 10px;
}
.qr-row .qr-img {
  width: 140px;
}
.qr-tip {
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.6;
  margin-top: 10px;
}
.btn-primary {
  display: block;
  width: 100%;
  height: 46px;
  background: var(--color-primary);
  color: #141414;
  border: none;
  border-radius: 2px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
}
.btn-ghost {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-border);
  border-radius: 2px;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
}
.fallback-tip {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-top: 10px;
}
.secondary {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(249, 212, 124, 0.15);
}
.secondary-label {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin-bottom: 10px;
}
.link {
  color: var(--color-primary);
  cursor: pointer;
  text-decoration: underline;
}
.donate-thanks {
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.6;
  margin-top: 20px;
}
.donate-close {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-top: 16px;
  cursor: pointer;
}
</style>
