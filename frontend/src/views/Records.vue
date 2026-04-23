<template>
  <div class="page records-page">
    <h2 class="page-title">{{ $t('卦例记录') }}</h2>
    <div v-if="records.length === 0" class="empty-state">{{ $t('暂无保存的卦例信息') }}</div>
    <div v-else class="record-list">
      <div class="record-item" v-for="record in records" :key="record.id">
        <div class="record-info touchable" @click="openRecord(record)">
          <span class="record-title">{{ record.title }}</span>
          <span v-if="record.messages" class="record-badge">{{ $t('已解卦') }}</span>
          <span v-else-if="record.yaoValues" class="record-badge badge-paipan">{{ $t('已排盘') }}</span>
          <span class="record-arrow">&#8250;</span>
        </div>
        <button class="rename-btn" @click="renameItem(record)">{{ $t('重命名') }}</button>
        <button class="delete-btn" @click="removeRecord(record.id)">{{ $t('删除') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRecords, deleteRecord, renameRecord } from '../store/records.js'
import { t } from '../utils/locale.js'

const router = useRouter()
const records = ref([])

onMounted(async () => {
  records.value = await getRecords()
})

function openRecord(record) {
  if (record.messages && record.messages.length > 0) {
    // 有聊天记录 → 恢复对话
    sessionStorage.setItem('liuyao_restoreRecordId', record.id)
    router.push('/chat')
  } else {
    // 纯排盘记录 → 打开排盘
    sessionStorage.setItem('liuyao_date', JSON.stringify({
      year: new Date(record.date).getFullYear(),
      month: new Date(record.date).getMonth() + 1,
      day: new Date(record.date).getDate(),
      hour: new Date(record.date).getHours()
    }))
    sessionStorage.setItem('liuyao_yaoValues', JSON.stringify(record.yaoValues))
    router.push('/hexagram')
  }
}

async function renameItem(record) {
  const newName = prompt(t('请输入新的名称'), record.title)
  if (newName !== null && newName.trim()) {
    await renameRecord(record.id, newName.trim())
    records.value = await getRecords()
  }
}

async function removeRecord(id) {
  if (confirm(t('确定要删除这条卦例记录吗？'))) {
    await deleteRecord(id)
    records.value = await getRecords()
  }
}
</script>

<style scoped>
.empty-state {
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 15px;
  margin-top: 60px;
}
.record-list {
  margin-top: 8px;
}
.record-item {
  display: flex;
  align-items: center;
  height: 60px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 1px;
  margin-bottom: 8px;
  padding: 0 12px;
}
.record-info {
  flex: 1;
  display: flex;
  align-items: center;
  cursor: pointer;
  height: 100%;
}
.record-title {
  flex: 1;
  color: var(--color-text);
  font-size: 16px;
}
.record-badge {
  color: var(--color-primary);
  font-size: 12px;
  margin-right: 6px;
  flex-shrink: 0;
}
.badge-paipan {
  color: var(--color-text-secondary);
}
.record-arrow {
  color: var(--color-text-secondary);
  font-size: 20px;
  margin-right: 8px;
}
.rename-btn {
  color: var(--color-primary);
  background: none;
  font-size: 14px;
  padding: 4px 8px;
}
.delete-btn {
  color: var(--color-danger);
  background: none;
  font-size: 14px;
  padding: 4px 8px;
}
</style>
