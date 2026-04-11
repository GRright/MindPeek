<template>
  <div class="features-view">
    <div class="features-container">
      <div class="features-header">
        <div class="header-left">
          <div class="stats-badge">
            <span class="stats-count">{{ features.length }}</span>
            <span class="stats-label">特征</span>
          </div>
          <div class="header-text">
            <h2 class="header-title">特征管理</h2>
            <p class="header-subtitle">查看和管理所有提取的用户特征</p>
          </div>
        </div>
        <div class="header-actions">
          <div class="alerts-trigger" v-if="insights.alerts.length > 0" @click="toggleAlerts">
            <el-icon :size="18"><Bell /></el-icon>
            <span class="alerts-badge">{{ insights.alerts.length }}</span>
          </div>
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
          <el-table-column prop="feature_type" label="特征类型" width="150">
            <template #default="{ row }">
              <el-tag :type="getFeatureTagType(row.feature_type)" size="small" effect="light">
                {{ row.feature_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="feature_value" label="特征值" min-width="220">
            <template #default="{ row }">
              <span class="feature-value-cell">{{ row.feature_value }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="confidence" label="置信度" width="180">
            <template #default="{ row }">
              <div class="confidence-cell">
                <div class="progress-wrapper">
                  <el-progress
                    :percentage="row.confidence * 100"
                    :stroke-width="8"
                    :color="getConfidenceColor(row.confidence)"
                    :show-text="false"
                    class="confidence-bar"
                  />
                </div>
                <span class="confidence-text">{{ (row.confidence * 100).toFixed(0) }}%</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="reasoning" label="推理依据" min-width="200" show-overflow-tooltip />
          <el-table-column prop="updated_at" label="更新时间" width="170">
            <template #default="{ row }">
              <span class="time-cell">{{ formatTime(row.updated_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
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
          <div class="empty-icon">
            <el-icon :size="48"><Document /></el-icon>
          </div>
          <p class="empty-text">暂无特征数据</p>
        </div>
      </div>
    </div>

    <Transition name="alerts-fade">
      <div class="alerts-dropdown" v-if="showAlerts && insights.alerts.length > 0">
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
    </Transition>
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

const showAlerts = ref(false)
let insightsAbortController = null

function toggleAlerts() {
  showAlerts.value = !showAlerts.value
}

function handleClickOutside(event) {
  if (!showAlerts.value) return
  const target = event.target
  const dropdown = document.querySelector('.alerts-dropdown')
  const trigger = document.querySelector('.alerts-trigger')
  if (dropdown && !dropdown.contains(target) && trigger && !trigger.contains(target)) {
    showAlerts.value = false
  }
}

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
  await loadFeatures()
  loadInsights()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (insightsAbortController) {
    insightsAbortController.abort()
  }
  document.removeEventListener('click', handleClickOutside)
})

async function loadFeatures() {
  loading.value = true
  try {
    const data = await store.loadProfile()
    features.value = data.features || []
  } catch (e) {
    console.error('Failed to load features:', e)
  } finally {
    loading.value = false
  }
}

async function loadInsights() {
  if (insightsAbortController) {
    insightsAbortController.abort()
  }
  insightsAbortController = new AbortController()
  
  try {
    const response = await axios.get(`/api/profile/${store.currentUserId}/insights`, {
      signal: insightsAbortController.signal,
      timeout: 30000
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
  if (confidence >= 0.8) return '#10b981'
  if (confidence >= 0.6) return '#f59e0b'
  return '#ef4444'
}

function tableRowClassName({ rowIndex }) {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row'
}
</script>

<style scoped>
.features-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.features-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.features-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
  padding: 24px;
  background: white;
  border-bottom: 1px solid var(--border-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stats-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.05) 100%);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.stats-count {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-primary);
  line-height: 1;
}

.stats-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.2;
}

.header-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  position: relative;
}

.alerts-trigger {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--text-secondary);
}

.alerts-trigger:hover {
  background: var(--bg-tertiary);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.alerts-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background: #ef4444;
  color: white;
  font-size: 10px;
  font-weight: 600;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-input {
  width: 220px;
}

.search-input :deep(.el-input__wrapper) {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  box-shadow: none;
  border-radius: var(--radius-md);
  padding: 8px 12px;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: var(--border-medium);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.search-input :deep(.el-input__inner) {
  color: var(--text-primary);
  font-size: 14px;
}

.filter-select {
  width: 150px;
}

.filter-select :deep(.el-input__wrapper) {
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  box-shadow: none;
  border-radius: var(--radius-md);
  padding: 8px 12px;
}

.filter-select :deep(.el-input__wrapper:hover) {
  border-color: var(--border-medium);
}

.filter-select :deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.filter-select :deep(.el-input__inner) {
  color: var(--text-primary);
  font-size: 14px;
}

.features-content {
  flex: 1;
  padding: 24px;
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
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-weight: 600;
  font-size: 13px;
  border-bottom: 1px solid var(--border-light);
}

.features-table :deep(.el-table__body-wrapper) {
  background: transparent;
}

.features-table :deep(.el-table__row) {
  background: transparent;
}

.features-table :deep(.el-table__row.even-row) {
  background: var(--bg-secondary);
}

.features-table :deep(.el-table__row:hover>td) {
  background: var(--bg-tertiary) !important;
}

.features-table :deep(.el-table__row td) {
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
  background: white !important;
}

.features-table :deep(.el-table__row.even-row td) {
  background: var(--bg-secondary) !important;
}

.features-table :deep(.el-table__row:hover > td) {
  background: var(--bg-tertiary) !important;
}

.feature-value-cell {
  font-weight: 500;
  color: var(--text-primary);
}

.confidence-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-wrapper {
  flex: 1;
}

.confidence-bar {
  flex: 1;
}

.confidence-text {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 36px;
  font-weight: 600;
}

.time-cell {
  font-size: 13px;
  color: var(--text-muted);
}

.delete-btn {
  color: var(--color-danger) !important;
}

.delete-btn:hover {
  opacity: 0.8;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  flex-shrink: 0;
}

.pagination-wrapper :deep(.el-pagination) {
  color: var(--text-secondary);
}

.pagination-wrapper :deep(.el-pagination button) {
  background: white;
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
}

.pagination-wrapper :deep(.el-pagination button:hover) {
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.pagination-wrapper :deep(.el-pager li) {
  background: white;
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  margin: 0 4px;
}

.pagination-wrapper :deep(.el-pager li:hover) {
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.pagination-wrapper :deep(.el-pager li.is-active) {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.empty-icon {
  color: var(--text-muted);
  margin-bottom: 16px;
}

.empty-text {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.alerts-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 1000;
  min-width: 340px;
  max-width: 400px;
}

.alerts-fade-enter-active,
.alerts-fade-leave-active {
  transition: all var(--transition-base);
}

.alerts-fade-enter-from,
.alerts-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.alerts-panel {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: 16px;
  max-height: 360px;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-light);
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  transition: all var(--transition-fast);
}

.alert-item:hover {
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
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.alert-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}

.alert-message {
  font-size: 12px;
  color: var(--text-secondary);
  word-break: break-word;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .features-view {
    height: auto;
    min-height: 100%;
  }
  
  .features-header {
    padding: 16px;
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
  }
  
  .search-input,
  .filter-select {
    width: 100%;
  }
  
  .features-content {
    padding: 16px;
    min-height: 250px;
  }
  
  .alerts-dropdown {
    left: 0;
    right: 0;
    min-width: auto;
    max-width: none;
  }
}
</style>
