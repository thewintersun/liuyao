import { fetchRecords, createServerRecord, updateServerRecord, deleteServerRecord } from '../api/index.js'

const STORAGE_KEY = 'liuyao_records'

function isLoggedIn() {
  return !!localStorage.getItem('liuyao_token')
}

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

/**
 * 本地时区的 ISO 格式（不带 Z / 时区偏移），如 2026-08-21T21:00:00
 * 不能用 toISOString()——那会转成 UTC，起卦时间会整体偏移时区差。
 * 无偏移的 ISO 字符串按 ES2015 规范由 new Date() 当作本地时间解析，往返一致，
 * 且字符串排序等价于时间排序。
 */
function toLocalISO(date) {
  const p = n => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())}`
    + `T${p(date.getHours())}:${p(date.getMinutes())}:${p(date.getSeconds())}`
}

// ========== localStorage 操作 ==========

function getLocalRecords() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

function saveLocalRecords(records) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(records))
}

// ========== 对外接口（全部 async） ==========

export async function getRecords() {
  if (isLoggedIn()) {
    try {
      const res = await fetchRecords()
      const serverRecords = res.records || []
      // 合并本地未迁移的记录
      const localRecords = getLocalRecords()
      if (localRecords.length > 0) {
        const serverIds = new Set(serverRecords.map(r => r.id))
        for (const local of localRecords) {
          if (!serverIds.has(local.id)) {
            try {
              await createServerRecord(local)
            } catch {
              // 迁移单条失败不影响整体
            }
          }
        }
        // 迁移完成后清除本地记录
        saveLocalRecords([])
        // 重新获取完整的服务器记录
        const updated = await fetchRecords()
        return updated.records || serverRecords
      }
      return serverRecords
    } catch {
      return getLocalRecords()
    }
  }
  return getLocalRecords()
}

export async function saveRecord(title, date, yaoValues) {
  const record = {
    id: generateId(),
    title: title,
    date: toLocalISO(date),
    yaoValues: yaoValues,
    createdAt: toLocalISO(new Date())
  }

  if (isLoggedIn()) {
    try {
      const res = await createServerRecord(record)
      return res.record
    } catch {
      // 服务器失败时降级到本地
      const records = getLocalRecords()
      records.unshift(record)
      saveLocalRecords(records)
      return record
    }
  }

  const records = getLocalRecords()
  records.unshift(record)
  saveLocalRecords(records)
  return record
}

export async function deleteRecord(id) {
  if (isLoggedIn()) {
    try {
      await deleteServerRecord(id)
      return
    } catch (e) {
      console.error('删除记录失败:', e)
      throw e
    }
  }
  const records = getLocalRecords()
  const filtered = records.filter(r => r.id !== id)
  saveLocalRecords(filtered)
}

export async function renameRecord(id, newTitle) {
  if (isLoggedIn()) {
    try {
      await updateServerRecord(id, { title: newTitle })
      return
    } catch (e) {
      console.error('重命名记录失败:', e)
      throw e
    }
  }
  const records = getLocalRecords()
  const record = records.find(r => r.id === id)
  if (record) {
    record.title = newTitle
    saveLocalRecords(records)
  }
}

export async function updateRecord(id, updates) {
  if (isLoggedIn()) {
    try {
      await updateServerRecord(id, updates)
      return
    } catch (e) {
      console.error('更新记录失败:', e)
      throw e
    }
  }
  const records = getLocalRecords()
  const record = records.find(r => r.id === id)
  if (record) {
    Object.assign(record, updates)
    saveLocalRecords(records)
  }
}

export async function getRecordById(id) {
  if (isLoggedIn()) {
    try {
      const records = await getRecords()
      return records.find(r => r.id === id) || null
    } catch {
      return null
    }
  }
  const records = getLocalRecords()
  return records.find(r => r.id === id) || null
}
