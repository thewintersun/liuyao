let currentLang = 'zh-CN'
let converter = null

function detectLang() {
  const saved = localStorage.getItem('liuyao_lang')
  if (saved && saved !== 'auto') return saved

  const nav = navigator.language || navigator.userLanguage || 'zh-CN'
  if (/^zh-(TW|HK|Hant)/i.test(nav)) return 'zh-TW'
  return 'zh-CN'
}

export function getLang() {
  return currentLang
}

export function isTraditional() {
  return currentLang === 'zh-TW'
}

export function setLang(lang) {
  localStorage.setItem('liuyao_lang', lang)
}

export async function initLocale() {
  currentLang = detectLang()

  if (isTraditional()) {
    try {
      const OpenCC = await import('opencc-js')
      converter = OpenCC.Converter({ from: 'cn', to: 'twp' })
    } catch (e) {
      console.warn('opencc-js load failed:', e)
      converter = null
    }
  }
}

export function t(text) {
  if (!text) return text
  if (!isTraditional() || !converter) return text
  return converter(text)
}
