import { reactive } from 'vue'

const state = reactive({
  toasts: []
})

let _id = 0

/**
 * 显示 Toast 提示
 * @param {string} message - 提示内容
 * @param {'success'|'error'|'warning'|'info'} [type='info'] - 提示类型
 * @param {number} [duration=2500] - 显示时长(ms)
 */
export function showToast(message, type = 'info', duration = 2500) {
  const id = ++_id
  state.toasts.push({ id, message, type, visible: true })
  setTimeout(() => {
    const t = state.toasts.find(t => t.id === id)
    if (t) t.visible = false
    setTimeout(() => {
      const idx = state.toasts.findIndex(t => t.id === id)
      if (idx !== -1) state.toasts.splice(idx, 1)
    }, 300)
  }, duration)
}

export function getToasts() {
  return state.toasts
}
