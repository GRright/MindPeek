<template>
  <div class="features-view">
    <div class="features-layout">
      <div class="left-panel" v-if="insights.alerts.length > 0">
        <div class="alerts-panel">
          <div class="panel-header">
            <el-icon :size="18"><Bell /></el-icon>
            <span>智能提醒</span>
          </div>
          <div class="alerts-list">
            <div 
              v-for="(alert, index) in insights.alerts" 
              :key="index"
              :class="['alert-item', alert.level]"
            >
              <el-icon :size="16" :class="alert.level">
                <component :is="getAlertIcon(alert.icon)" />
              </el-icon>
              <div class="alert-content">
                <span class="alert-title">{{ alert.title }}</span>
                <span class="alert-message">{{ alert.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="right-panel">
        <div class="features-header">
          <div class="header-left">
            <el-icon :size="20"><Document /></el-icon>
            <span class="header-title">特征管理</span>
            <span class="feature-count" v-if="features.length > 0">共 {{ features.length }} 个特征</span>
          </div>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索特征..."
              clearable
              class="search-input"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select
              v-model="selectedTypes"
              multiple
              collapse-tags
              collapse-tags-tooltip
              placeholder="筛选类型"
              class="filter-select"
            >
              <el-option
                v-for="type in featureTypes"
                :key="type"
                :label="type"
                :value="type"
              />
            </el-select>
          </div>
        </div>

        <div class="features-content">
          <el-table
            :data="paginatedFeatures"
            style="width: 100%"
            v-loading="loading"
            class="features-table"
            :row-class-name="tableRowClassName"
          >
            <el-table-column prop="feature_type" label="特征类型" width="140">
              <template #default="{ row }">
                <el-tag :type="getFeatureTagType(row.feature_type)" size="small">
                  {{ row.feature_type }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="feature_value" label="特征值" min-width="200">
              <template #default="{ row }">
                <span class="feature-value-cell">{{ row.feature_value }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="confidence" label="置信度" width="160">
              <template #default="{ row }">
                <div class="confidence-cell">
                  <el-progress
                    :percentage="row.confidence * 100"
                    :stroke-width="6"
                    :color="getConfidenceColor(row.confidence)"
                    :show-text="false"
                    class="confidence-bar"
                  />
                  <span class="confidence-text">{{ (row.confidence * 100).toFixed(0) }}%</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="reasoning" label="推理依据" min-width="180" show-overflow-tooltip />
            <el-table-column prop="updated_at" label="更新时间" width="160">
              <template #default="{ row }">
                <span class="time-cell">{{ formatTime(row.updated_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="deleteFeature(row)"
                  class="delete-btn"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrapper" v-if="filteredTotal > pageSize">
            <el-pagination
              :current-page="currentPage"
              @update:current-page="currentPage = $event"
              :page-size="pageSize"
              :total="filteredTotal"
              layout="total, prev, pager, next"
            />
          </div>

          <div class="empty-state" v-if="!loading && features.length === 0">
            <el-icon :size="48"><Document /></el-icon>
            <p>暂无特征数据</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProfileStore } from '@/stores/profile'
import { Document, Search, Bell, Warning, SuccessFilled, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'

const store = useProfileStore()

const features = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const selectedTypes = ref([])

const insights = ref({
  alerts: [],
  stats: {}
})

let abortController = null

const showAddDialog = ref(false)
const adding = ref(false)
const newFeature = ref({
  feature_type: '',
  feature_value: '',
  confidence: 0.7,
  source_message: '',
  reasoning: ''
})

const featureTypes = computed(() => {
  const types = new Set(features.value.map(f => f.feature_type))
  return Array.from(types).sort()
})

const filteredFeatures = computed(() => {
  let result = features.value
  
  if (selectedTypes.value.length > 0) {
    result = result.filter(f => selectedTypes.value.includes(f.feature_type))
  }
  
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(f => 
      f.feature_type.toLowerCase().includes(query) ||
      f.feature_value.toLowerCase().includes(query) ||
      (f.reasoning && f.reasoning.toLowerCase().includes(query))
    )
  }
  
  return result
})

const filteredTotal = computed(() => filteredFeatures.value.length)

const paginatedFeatures = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredFeatures.value.slice(start, end)
})

watch([searchQuery, selectedTypes], () => {
  currentPage.value = 1
})

onMounted(async () => {
  await Promise.all([
    loadFeatures(),
    loadInsights()
  ])
})

onUnmounted(() => {
  if (abortController) {
    abortController.abort()
  }
})

async function loadFeatures() {
  loading.value = true
  try {
    const data = await store.loadProfile()
    features.value = data.features || []
  } catch (e) {
    if (e.name !== 'AbortError' && e.code !== 'ERR_CANCELED') {
      console.error('Failed to load features:', e)
    }
  } finally {
    loading.value = false
  }
}

async function loadInsights() {
  if (abortController) {
    abortController.abort()
  }
  abortController = new AbortController()
  
  try {
    const response = await axios.get(`/api/profile/${store.currentUserId}/insights`, {
      signal: abortController.signal
    })
    const data = response.data
    data.alerts = data.alerts.filter(alert => 
      !alert.title.includes('更新') && !alert.title.includes('update')
    )
    insights.value = data
  } catch (e) {
    if (e.name !== 'AbortError' && e.code !== 'ERR_CANCELED') {
      console.error('Failed to load insights:', e)
    }
  }
}

function getAlertIcon(iconType) {
  const icons = {
    'warning': Warning,
    'success': SuccessFilled,
    'update': Refresh
  }
  return icons[iconType] || Warning
}

async function addFeature() {
  if (!newFeature.value.feature_type || !newFeature.value.feature_value) {
    ElMessage.warning('请填写特征类型和特征值')
    return
  }

  adding.value = true
  try {
    await store.addFeature(newFeature.value)
    ElMessage.success('添加成功')
    showAddDialog.value = false
    newFeature.value = {
      feature_type: '',
      feature_value: '',
      confidence: 0.7,
      source_message: '',
      reasoning: ''
    }
    await loadFeatures()
  } catch (e) {
    ElMessage.error('添加失败: ' + e.message)
  } finally {
    adding.value = false
  }
}

async function deleteFeature(row) {
  try {
    await ElMessageBox.confirm('确定要删除这个特征吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await store.deleteFeature(row.id)
    ElMessage.success('删除成功')
    await loadFeatures()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function formatTime(timestamp) {
  if (!timestamp) return '暂无数据'
  try {
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return '暂无数据'
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    console.error('时间格式化失败:', e)
    return '暂无数据'
  }
}

function getFeatureTagType(type) {
  const types = {
    'MBTI': 'primary',
    '大五人格': 'success',
    '行为习惯': 'warning',
    '潜在想法': 'danger',
    '兴趣爱好': 'info'
  }
  return types[type] || 'info'
}

function getConfidenceColor(confidence) {
  if (confidence >= 0.8) return '#22c55e'
  if (confidence >= 0.6) return '#f59e0b'
  return '#ef4444'
}

function tableRowClassName({ rowIndex }) {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row'
}
</script>

<style scoped>
.features-view {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 7rem);
  min-height: 400px;
  overflow: hidden;
}

.features-layout {
  display: grid;
  grid-template-columns: 18.75rem 1fr;
  gap: 1.25rem;
  height: 100%;
}

.left-panel {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.right-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.alerts-panel {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1rem;
  height: 100%;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 0.875rem;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.625rem 0.75rem;
  border-radius: 0.5rem;
  background: var(--bg-tertiary);
}

.alert-item.warning {
  border-left: 3px solid #f59e0b;
}

.alert-item.serious {
  border-left: 3px solid #ef4444;
}

.alert-item.info {
  border-left: 3px solid #22c55e;
}

.alert-item .warning {
  color: #f59e0b;
}

.alert-item .serious {
  color: #ef4444;
}

.alert-item .success {
  color: #22c55e;
}

.alert-content {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  flex: 1;
  min-width: 0;
}

.alert-title {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-primary);
}

.alert-message {
  font-size: 0.75rem;
  color: var(--text-secondary);
  word-break: break-word;
}

.features-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  color: var(--text-primary);
}

.header-title {
  font-size: 1rem;
  font-weight: 600;
}

.feature-count {
  font-size: 0.75rem;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 0.125rem 0.5rem;
  border-radius: 0.625rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.search-input {
  width: 12.5rem;
  max-width: 100%;
}

.search-input :deep(.el-input__wrapper) {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  box-shadow: none;
}

.search-input :deep(.el-input__inner) {
  color: var(--text-primary);
}

.filter-select {
  width: 11.25rem;
  max-width: 100%;
}

.filter-select :deep(.el-input__wrapper) {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  box-shadow: none;
}

.filter-select :deep(.el-input__inner) {
  color: var(--text-primary);
}

.features-content {
  flex: 1;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 0.75rem;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 300px;
}

.features-table {
  background: transparent;
  flex: 1;
}

.features-table :deep(.el-table__header-wrapper th) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
}

.features-table :deep(.el-table__body-wrapper) {
  background: transparent;
}

.features-table :deep(.el-table__row) {
  background: transparent;
}

.features-table :deep(.el-table__row.even-row) {
  background: var(--bg-tertiary);
}

.features-table :deep(.el-table__row:hover>td) {
  background: var(--bg-hover) !important;
}

.features-table :deep(.el-table__row td) {
  border-bottom: 1px solid var(--border-color);
  color: var(--text-primary);
  background: var(--bg-secondary) !important;
}

.features-table :deep(.el-table__row.even-row td) {
  background: var(--bg-tertiary) !important;
}

.features-table :deep(.el-table__row:hover > td) {
  background: var(--bg-hover) !important;
}

.feature-value-cell {
  font-weight: 500;
}

.confidence-cell {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.confidence-bar {
  flex: 1;
}

.confidence-text {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  min-width: 2.5rem;
}

.time-cell {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.delete-btn {
  color: var(--danger-color) !important;
}

.delete-btn:hover {
  opacity: 0.8;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 1.25rem;
  flex-shrink: 0;
}

.pagination-wrapper :deep(.el-pagination) {
  color: var(--text-secondary);
}

.pagination-wrapper :deep(.el-pagination button) {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.pagination-wrapper :deep(.el-pager li) {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.pagination-wrapper :deep(.el-pager li.is-active) {
  background: var(--accent-color);
  color: white;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3.75rem 1.25rem;
  color: var(--text-muted);
}

.empty-state p {
  margin-top: 0.75rem;
  font-size: 0.875rem;
}

@media screen and (max-width: 768px) {
  .features-view {
    height: auto;
    min-height: calc(100vh - 7rem);
  }
  
  .features-layout {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr;
    height: auto;
  }
  
  .left-panel {
    display: none;
  }
  
  .features-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    width: 100%;
  }
  
  .search-input,
  .filter-select {
    width: 100%;
  }
  
  .features-content {
    padding: 0.75rem;
    min-height: 250px;
  }
}

@media screen and (min-width: 1920px) {
  .features-view {
    max-width: 1400px;
    margin: 0 auto;
  }
}
</style>
