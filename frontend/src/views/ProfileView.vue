<template>
  <div class="profile-view">
    <div class="profile-grid">
      <div class="profile-sidebar">
        <div class="user-card card-animate">
          <div class="user-avatar">
            <div class="avatar-ring">
              <div class="avatar-inner">
                {{ userId.charAt(0).toUpperCase() }}
              </div>
            </div>
          </div>
          <h2 class="user-name">{{ userId }}</h2>
          <div class="user-badge" v-if="profileSummary?.mbti">
            <span class="mbti-badge">{{ profileSummary.mbti }}</span>
          </div>

          <div class="user-stats">
            <div class="stat-item">
              <span class="stat-value">{{ profileSummary?.feature_count || 0 }}</span>
              <span class="stat-label">特征数</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-value">{{ profileSummary?.conversation_count || 0 }}</span>
              <span class="stat-label">对话轮数</span>
            </div>
            <div class="stat-divider"></div>
            <div class="stat-item">
              <span class="stat-value">{{ confidencePercent }}%</span>
              <span class="stat-label">置信度</span>
            </div>
          </div>
        </div>

        <div class="overview-card card-animate">
          <div class="card-title">用户画像概述</div>
          <div class="overview-content">
            <div class="overview-item">
              <span class="overview-label">职业</span>
              <span class="overview-value">{{ getFeatureValueByType('职业') || '未知' }}</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">性格</span>
              <span class="overview-value">{{ getMbtiSummary() }}</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">兴趣</span>
              <span class="overview-value">{{ getTopInterests() }}</span>
            </div>
            <div class="overview-item">
              <span class="overview-label">生活方式</span>
              <span class="overview-value">{{ getLifestyleSummary() }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="profile-main">
        <div class="charts-card card-animate">
          <div class="card-header">
            <span class="card-title">用户画像分析</span>
            <el-button text @click="refreshProfile" class="refresh-btn">
              <el-icon :size="18"><Refresh /></el-icon>
            </el-button>
          </div>

          <el-tabs v-model="activeTab" class="profile-tabs">
            <el-tab-pane label="雷达图" name="radar">
              <div ref="radarContainer" class="chart-container"></div>
            </el-tab-pane>
            <el-tab-pane label="关系图" name="graph">
              <div ref="graphContainer" class="chart-container"></div>
            </el-tab-pane>
            <el-tab-pane label="分布图" name="pie">
              <div ref="pieContainer" class="chart-container"></div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <div class="features-card">
          <div class="card-header">
            <span class="card-title">详细特征</span>
            <span class="feature-count">{{ filteredFeatures.length }} 个特征</span>
          </div>

          <div class="search-container">
            <el-input
              v-model="searchQuery"
              placeholder="搜索特征类型或内容..."
              clearable
              prefix-icon="Search"
              class="search-input"
            />
          </div>

          <div 
            ref="timelineContainer" 
            class="features-timeline"
            @scroll="handleScroll"
          >
            <div
              v-for="(feature, index) in displayedFeatures"
              :key="feature.id || index"
              class="timeline-item"
            >
              <div class="timeline-dot" :style="{ background: getFeatureColor(feature.feature_type) }"></div>
              <div class="timeline-content">
                <div class="feature-header">
                  <div class="feature-tags">
                    <el-tag :type="getFeatureTagType(feature.feature_type)" size="small">
                      {{ feature.feature_type }}
                    </el-tag>
                    <el-tag v-if="feature.verification_count > 0" type="success" size="small" effect="dark">
                      已验证 {{ feature.verification_count }} 次
                    </el-tag>
                  </div>
                  <span class="confidence">{{ (feature.confidence * 100).toFixed(0) }}%</span>
                </div>
                <div class="feature-value">{{ feature.feature_value }}</div>
                <div v-if="feature.reasoning" class="feature-reasoning">
                  {{ feature.reasoning }}
                </div>
              </div>
            </div>

            <div v-if="hasMore && filteredFeatures.length > 0" class="loading-more">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>加载中...</span>
            </div>

            <div v-if="filteredFeatures.length === 0" class="empty-features">
              <el-icon :size="48"><Document /></el-icon>
              <p>{{ searchQuery ? '未找到匹配的特征' : '暂无特征数据' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, watch, nextTick } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useRoute, onBeforeRouteUpdate } from 'vue-router'
import * as echarts from 'echarts'
import { Refresh, Document, Loading, Search } from '@element-plus/icons-vue'

const store = useProfileStore()
const route = useRoute()

const activeTab = ref('radar')
const profileSummary = ref(null)
const allFeatures = ref([])

const searchQuery = ref('')
const timelineContainer = ref(null)
const itemsPerLoad = 10
const displayedCount = ref(itemsPerLoad)

const userId = computed(() => store.currentUserId)

const radarContainer = ref(null)
const graphContainer = ref(null)
const pieContainer = ref(null)

let radarChart = null
let graphChart = null
let pieChart = null

const mbtiActive = ref([false, false, false, false])

const confidencePercent = computed(() => {
  if (!profileSummary.value?.confidence_score) return 0
  return (profileSummary.value.confidence_score * 100).toFixed(0)
})

const filteredFeatures = computed(() => {
  if (!searchQuery.value) {
    return allFeatures.value
  }
  const query = searchQuery.value.toLowerCase()
  return allFeatures.value.filter(feature => 
    feature.feature_type.toLowerCase().includes(query) ||
    feature.feature_value.toLowerCase().includes(query) ||
    (feature.reasoning && feature.reasoning.toLowerCase().includes(query))
  )
})

const displayedFeatures = computed(() => {
  return filteredFeatures.value.slice(0, displayedCount.value)
})

const hasMore = computed(() => {
  return displayedCount.value < filteredFeatures.value.length
})

// 获取指定类型的特征值
function getFeatureValueByType(type) {
  const feature = allFeatures.value.find(f => f.feature_type === type)
  return feature ? feature.feature_value : null
}

// 获取 MBTI 总结
function getMbtiSummary() {
  const mbtiFeature = allFeatures.value.find(f => f.feature_type === 'MBTI')
  if (mbtiFeature) {
    const value = mbtiFeature.feature_value
    // 提取 MBTI 类型（如 INFP、INTP）
    const match = value.match(/[A-Z]{4}/)
    if (match) return match[0]
    return value.slice(0, 10) + (value.length > 10 ? '...' : '')
  }
  return '未知'
}

// 获取主要兴趣
function getTopInterests() {
  const interests = allFeatures.value
    .filter(f => f.feature_type === '兴趣爱好')
    .slice(0, 3)
    .map(f => f.feature_value)
  return interests.length ? interests.join('、') : '暂无'
}

// 获取生活方式总结
function getLifestyleSummary() {
  const habits = allFeatures.value
    .filter(f => f.feature_type === '行为习惯')
    .slice(0, 2)
    .map(f => f.feature_value)
  return habits.length ? habits.join('、') : '暂无'
}

onMounted(async () => {
  await loadProfile()

  const handleRefresh = (event) => {
    if (event.detail && event.detail.userId === userId.value) {
      loadProfile()
    }
  }
  window.addEventListener('profileNeedsRefresh', handleRefresh)
})

onActivated(async () => {
  await loadProfile()
})

onBeforeRouteUpdate(async (to, from) => {
  await loadProfile()
})

watch(activeTab, () => {
  nextTick(() => {
    if (activeTab.value === 'radar' && profileSummary.value) renderRadarChart()
    else if (activeTab.value === 'graph' && allFeatures.value.length) renderGraphChart()
    else if (activeTab.value === 'pie' && allFeatures.value.length) renderPieChart()
  })
})

watch(allFeatures, () => {
  nextTick(() => {
    if (profileSummary.value) renderRadarChart()
    if (allFeatures.value.length) {
      renderGraphChart()
      renderPieChart()
    }
  })
}, { deep: true })

async function loadProfile() {
  try {
    const data = await store.loadProfile()
    profileSummary.value = data.summary
    allFeatures.value = data.features || []
    displayedCount.value = itemsPerLoad
    await nextTick()
    renderRadarChart()
  } catch (e) {
    console.error('Failed to load profile:', e)
  }
}

async function refreshProfile() {
  try {
    // 先触发分析任务
    const analyzeResponse = await fetch(`/api/profile/${userId.value}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (analyzeResponse.ok) {
      ElMessage.success('已触发用户画像分析任务，后台处理中...')
    }
    
    // 然后重新加载数据
    await loadProfile()
    ElMessage.success('用户画像已更新')
  } catch (e) {
    console.error('刷新失败:', e)
    ElMessage.error('刷新失败：' + e.message)
  }
}

watch(searchQuery, () => {
  displayedCount.value = itemsPerLoad
  nextTick(() => {
    if (timelineContainer.value) {
      timelineContainer.value.scrollTop = 0
    }
  })
})

function handleScroll() {
  if (!timelineContainer.value || !hasMore.value) return
  
  const container = timelineContainer.value
  const { scrollTop, scrollHeight, clientHeight } = container
  
  if (scrollTop + clientHeight >= scrollHeight - 100) {
    displayedCount.value += itemsPerLoad
  }
}

function renderRadarChart() {
  if (!radarContainer.value) return

  if (radarChart) {
    radarChart.dispose()
  }
  radarChart = echarts.init(radarContainer.value)

  const bigFiveData = profileSummary.value?.big_five || {}
  const indicators = [
    { name: '开放性', max: 100 },
    { name: '尽责性', max: 100 },
    { name: '外向性', max: 100 },
    { name: '宜人性', max: 100 },
    { name: '神经质', max: 100 }
  ]

  const values = [
    parseInt(bigFiveData['开放性'] || 50),
    parseInt(bigFiveData['尽责性'] || 50),
    parseInt(bigFiveData['外向性'] || 50),
    parseInt(bigFiveData['宜人性'] || 50),
    parseInt(bigFiveData['神经质'] || 50)
  ]

  const option = {
    backgroundColor: '#ffffff',
    animation: true,
    animationDuration: 1500,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      borderColor: '#333333',
      textStyle: { color: '#ffffff', fontSize: 14 }
    },
    radar: {
      indicator: indicators,
      radius: '65%',
      axisName: {
        color: '#000000',
        fontSize: 18,
        fontWeight: 900,
        padding: [10, 10, 10, 10],
        textShadowColor: 'rgba(255, 255, 255, 0.9)',
        textShadowBlur: 3
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(99, 102, 241, 0.05)', 'rgba(99, 102, 241, 0.1)']
        }
      },
      splitLine: {
        lineStyle: { color: '#666666', width: 1.5 }
      },
      axisLine: {
        lineStyle: { color: '#333333', width: 2 }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '大五人格',
        areaStyle: {
          color: 'rgba(99, 102, 241, 0.3)'
        },
        lineStyle: {
          color: '#6366f1',
          width: 3
        },
        itemStyle: {
          color: '#6366f1',
          borderWidth: 2
        },
        label: {
          show: true,
          color: '#000000',
          fontSize: 14,
          fontWeight: 900,
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          padding: [2, 6, 2, 6],
          borderRadius: 4
        }
      }]
    }]
  }

  radarChart.setOption(option)
}

function renderGraphChart() {
  if (!graphContainer.value) return

  if (graphChart) {
    graphChart.dispose()
  }
  graphChart = echarts.init(graphContainer.value)

  const displayFeatures = allFeatures.value.filter(f => f.confidence > 0)
  
  if (displayFeatures.length === 0) {
    const option = {
      backgroundColor: 'transparent',
      title: {
        text: '暂无特征数据',
        left: 'center',
        top: 'center',
        textStyle: { color: 'var(--text-muted)', fontSize: 14 }
      }
    }
    graphChart.setOption(option)
    return
  }

  const existingTypes = [...new Set(displayFeatures.map(f => f.feature_type))]
  const categories = existingTypes

  // 使用 Map 去重，确保节点名称唯一
  const uniqueFeatures = []
  const seenValues = new Set()
  displayFeatures.forEach(f => {
    if (!seenValues.has(f.feature_value)) {
      seenValues.add(f.feature_value)
      uniqueFeatures.push(f)
    }
  })
  
  const nodes = uniqueFeatures.slice(0, 15).map((f, idx) => ({
    id: `feature_${idx}`,
    name: f.feature_value,
    category: categories.indexOf(f.feature_type),
    value: f.confidence,
    symbolSize: 15 + f.confidence * 20
  }))

  nodes.unshift({
    id: 'user',
    name: userId.value,
    category: categories.length,
    symbolSize: 30,
    value: 1
  })

  const links = uniqueFeatures.slice(0, 10).map((f, idx) => ({
    source: 'user',
    target: `feature_${idx}`,
    lineStyle: {
      width: f.confidence * 2,
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [
          { offset: 0, color: '#6366f1' },
          { offset: 1, color: getFeatureColor(f.feature_type) }
        ]
      }
    }
  }))

  const allCategoriesWithUser = [...categories, '用户']
  
  const option = {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1500,
    animationEasing: 'cubicOut',
    tooltip: {
      formatter: '{b}',
      backgroundColor: 'var(--bg-tertiary)',
      borderColor: 'var(--border-color)',
      textStyle: { color: 'var(--text-primary)' }
    },
    legend: categories.length > 0 ? [{
      data: allCategoriesWithUser,
      textStyle: { color: 'var(--text-primary)', fontSize: 12 }
    }] : undefined,
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      label: {
        show: true,
        position: 'right',
        fontSize: 11,
        color: 'var(--text-primary)'
      },
      categories: allCategoriesWithUser.map((name, idx) => ({ name, itemStyle: { color: idx < categories.length ? getFeatureColor(name) : '#ec4899' } })),
      nodes: nodes,
      links: links,
      lineStyle: {
        curveness: 0.3,
        color: 'source'
      },
      emphasis: {
        focus: 'adjacency'
      },
      force: {
        repulsion: 150,
        edgeLength: [60, 180]
      }
    }]
  }

  graphChart.setOption(option)
}

function renderPieChart() {
  if (!pieContainer.value) return

  if (pieChart) {
    pieChart.dispose()
  }
  pieChart = echarts.init(pieContainer.value)

  const typeCount = {}
  allFeatures.value.forEach(f => {
    typeCount[f.feature_type] = (typeCount[f.feature_type] || 0) + 1
  })

  const pieData = Object.entries(typeCount).map(([name, value]) => ({
    name,
    value
  }))

  const option = {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1500,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'var(--bg-tertiary)',
      borderColor: 'var(--border-color)',
      textStyle: { color: 'var(--text-primary)' }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: { color: 'var(--text-secondary)', fontSize: 11 }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 8,
        borderColor: 'var(--bg-secondary)',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold',
          color: 'var(--text-primary)'
        }
      },
      labelLine: {
        show: false
      },
      data: pieData,
      color: ['#6366f1', '#ef4444', '#f59e0b', '#22c55e', '#2196f3', '#8b5cf6']
    }]
  }

  pieChart.setOption(option)
}

function getFeatureColor(type) {
  const predefinedColors = {
    'MBTI': '#8b5cf6',
    '大五人格': '#2196f3',
    '行为习惯': '#f59e0b',
    '潜在想法': '#ef4444',
    '兴趣爱好': '#22c55e',
    '用户信息': '#ec4899'
  }
  if (predefinedColors[type]) {
    return predefinedColors[type]
  }
  const colors = ['#8b5cf6', '#2196f3', '#f59e0b', '#ef4444', '#22c55e', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#a855f7']
  let hash = 0
  for (let i = 0; i < type.length; i++) {
    hash = type.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

function getFeatureTagType(type) {
  const predefinedTypes = {
    'MBTI': 'primary',
    '大五人格': 'success',
    '行为习惯': 'warning',
    '潜在想法': 'danger',
    '兴趣爱好': 'info',
    '用户信息': ''
  }
  if (predefinedTypes.hasOwnProperty(type)) {
    return predefinedTypes[type]
  }
  const types = ['primary', 'success', 'warning', 'danger', 'info', '']
  let hash = 0
  for (let i = 0; i < type.length; i++) {
    hash = type.charCodeAt(i) + ((hash << 5) - hash)
  }
  return types[Math.abs(hash) % types.length]
}

function highlightMbti(idx) {
  mbtiActive.value = mbtiActive.value.map((_, i) => i === idx)
}

function resetMbti() {
  mbtiActive.value = [false, false, false, false]
}

function getMbtiCharLabel(char) {
  const meanings = {
    'I': '内向',
    'E': '外向',
    'N': '直觉',
    'S': '感觉',
    'T': '思考',
    'F': '情感',
    'J': '判断',
    'P': '感知'
  }
  return meanings[char] || ''
}
</script>

<style scoped>
.profile-view {
  height: calc(100vh - 112px);
  overflow-y: auto;
}

.profile-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
}

.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.user-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.user-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
}

.user-avatar {
  margin-bottom: 16px;
}

.avatar-ring {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 4px;
  margin: 0 auto;
}

.avatar-inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
}

.user-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.user-badge {
  margin-bottom: 20px;
}

.mbti-badge {
  display: inline-block;
  padding: 6px 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  color: white;
}

.user-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 20px;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--border-color);
}

.user-input-section {
  padding-top: 8px;
}

.user-id-input {
  width: 100%;
}

.user-id-input :deep(.el-input__wrapper) {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  box-shadow: none;
}

.user-id-input :deep(.el-input__inner) {
  color: var(--text-primary);
}

.overview-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.overview-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.overview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: var(--bg-tertiary);
  border-radius: 10px;
}

.overview-label {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}

.overview-value {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 600;
  max-width: 60%;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mbti-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.mbti-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
}

.mbti-chars {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.mbti-char-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mbti-char-item:hover,
.mbti-char-item.active {
  background: var(--accent-color);
}

.mbti-char {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.mbti-char-item.active .mbti-char {
  color: white;
}

.mbti-label {
  font-size: 11px;
  color: var(--text-muted);
}

.mbti-char-item.active .mbti-label {
  color: rgba(255, 255, 255, 0.8);
}

.profile-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.charts-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.refresh-btn {
  color: var(--text-secondary);
}

.refresh-btn:hover {
  color: var(--accent-color);
}

.profile-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}

.profile-tabs :deep(.el-tabs__item) {
  color: var(--text-secondary);
}

.profile-tabs :deep(.el-tabs__item.is-active) {
  color: var(--accent-color);
}

.profile-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--accent-color);
}

.chart-container {
  height: 350px;
}

.features-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.search-container {
  margin-bottom: 16px;
}

.search-input {
  width: 100%;
}

.feature-count {
  font-size: 13px;
  color: var(--text-muted);
}

.features-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
}

.features-timeline::-webkit-scrollbar {
  width: 6px;
}

.features-timeline::-webkit-scrollbar-track {
  background: var(--bg-tertiary);
  border-radius: 3px;
}

.features-timeline::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.features-timeline::-webkit-scrollbar-thumb:hover {
  background: var(--accent-color);
}

.loading-more {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  color: var(--text-muted);
  font-size: 13px;
}

.timeline-item {
  display: flex;
  gap: 14px;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.timeline-content {
  flex: 1;
  padding: 14px;
  background: var(--bg-tertiary);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.feature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}

.feature-tags {
  display: flex;
  gap: 8px;
  align-items: center;
}

.confidence {
  font-size: 13px;
  color: var(--text-secondary);
}

.feature-value {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.feature-reasoning {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.4;
}

.empty-features {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.empty-features p {
  margin-top: 12px;
  font-size: 14px;
}
</style>