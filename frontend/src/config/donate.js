/**
 * 捐助配置
 *
 * 填写说明：
 * 1. wechatQr / alipayQr —— 收款码图片，放到 frontend/public/donate/ 目录下，
 *    这里填以 / 开头的绝对路径（如 '/donate/wechat.png'）。
 *    微信码请用「赞赏码」或「收款码」截图，四周留白，不要加圆角遮罩，否则影响识别。
 * 2. alipayUrl —— 支付宝个人收款码对应的短链，形如 https://qr.alipay.com/xxxxxxxx
 *    获取方式：支付宝 App → 收钱 → 右上角保存/分享 → 复制链接。
 *    注意：个人收款码无法预填金额，用户需自行输入。
 *
 * 三项留空时，设置页不会显示捐助入口（避免露出半成品）。
 */
export const DONATE_CONFIG = {
  wechatQr: '',
  alipayQr: '',
  alipayUrl: ''
}

/** 是否已配置（任一渠道可用即可） */
export function isDonateEnabled() {
  const { wechatQr, alipayQr, alipayUrl } = DONATE_CONFIG
  return !!(wechatQr || alipayQr || alipayUrl)
}
