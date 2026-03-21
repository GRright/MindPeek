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
              <span class="stat-value">{{ profileSummary?.total_features || 0 }}</span>
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

        <div class="mbti-card card-animate" v-if="profileSummary?.mbti">
          <div class="card-title">MBTI 性格解析</div>
          <div class="mbti-chars">
            <div
              v-for="(char, idx) in profileSummary.mbti.split('')"
              :key="idx"
              class="mbti-char-item"
              @mouseenter="highlightMbti(idx)"
              @mouseleave="resetMbti"
              :class="{ active: mbtiActive[idx] }"
            >
              <span class="mbti-char">{{ char }}</span>
              <span class="mbti-label">{{ getMbtiCharLabel(char) }}</span>
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
            <span class="feature-count">{{ allFeatures.length }} 个特征</span>
          </div>

          <div class="features-timeline">
            <div
              v-for="(feature, index) in allFeatures"
              :key="index"
              class="timeline-item"
            >
              <div class="timeline-dot" :style="{ background: getFeatureColor(feature.feature_type) }"></div>
              <div class="timeline-content">
                <div class="feature-header">
                  <el-tag :type="getFeatureTagType(feature.feature_type)" size="small">
                    {{ feature.feature_type }}
                  </el-tag>
                  <span class="confidence">{{ (feature.confidence * 100).toFixed(0) }}%</span>
                </div>
                <div class="feature-value">{{ feature.feature_value }}</div>
                <div v-if="feature.reasoning" class="feature-reasoning">
                  {{ feature.reasoning }}
                </div>
              </div>
            </div>

            <div v-if="allFeatures.length === 0" class="empty-features">
              <el-icon :size="48"><Document /></el-icon>
              <p>暂无特征数据</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useProfileStore } from '@/stores/profile'
import * as echarts from 'echarts'
import { Refresh, Document } from '@element-plus/icons-vue'

const store = useProfileStore()

const activeTab = ref('radar')
const profileSummary = ref(null)
const allFeatures = ref([])

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

onMounted(async () => {
  await loadProfile()
})

watch(activeTab, () => {
  nextTick(() => {
    if (activeTab.value === 'radar' && profileSummary.value) renderRadarChart()
    else if (activeTab.value === 'graph' && allFeatures.value.length) renderGraphChart()
    else if (activeTab.value === 'pie' && allFeatures.value.length) renderPieChart()
  })
})

async function loadProfile() {
  try {
    const data = await store.loadProfile()
    profileSummary.value = data.summary
    allFeatures.value = data.features || []
    await nextTick()
    renderRadarChart()
  } catch (e) {
    console.error('Failed to load profile:', e)
  }
}

async function refreshProfile() {
  await loadProfile()
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
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1500,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'var(--bg-tertiary)',
      borderColor: 'var(--border-color)',
      textStyle: { color: 'var(--text-primary)' }
    },
    radar: {
      indicator: indicators,
      radius: '65%',
      axisName: {
        color: 'var(--text-secondary)',
        fontSize: 12
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(99, 102, 241, 0.05)', 'rgba(99, 102, 241, 0.1)']
        }
      },
      splitLine: {
        lineStyle: { color: 'var(--border-color)' }
      },
      axisLine: {
        lineStyle: { color: 'var(--border-color)' }
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
          width: 2
        },
        itemStyle: {
          color: '#6366f1'
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

  const categories = ['MBTI', '大五人格', '行为习惯', '潜在想法', '兴趣爱好']

  const nodes = allFeatures.value.slice(0, 15).map((f, idx) => ({
    name: f.feature_value,
    category: categories.indexOf(f.feature_type) >= 0 ? categories.indexOf(f.feature_type) : 4,
    value: f.confidence,
    symbolSize: 30 + f.confidence * 40
  }))

  nodes.unshift({
    name: userId.value,
    category: 5,
    symbolSize: 60,
    value: 1
  })

  const links = allFeatures.value.slice(0, 10).map(f => ({
    source: userId.value,
    target: f.feature_value,
    lineStyle: {
      width: f.confidence * 3,
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
    legend: [{
      data: categories,
      textStyle: { color: 'var(--text-secondary)', fontSize: 10 }
    }],
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      label: {
        show: true,
        position: 'right',
        fontSize: 10,
        color: 'var(--text-primary)'
      },
      categories: categories.map((name, idx) => ({ name, itemStyle: { color: getCategoryColor(idx) } })),
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
        repulsion: 100,
        edgeLength: [50, 150]
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

function getCategoryColor(idx) {
  const colors = ['#8b5cf6', '#2196f3', '#f59e0b', '#ef4444', '#22c55e', '#ec4899']
  return colors[idx] || '#6b6c7d'
}

function getFeatureColor(type) {
  const colors = {
    'MBTI': '#8b5cf6',
    '大五人格': '#2196f3',
    '行为习惯': '#f59e0b',
    '潜在想法': '#ef4444',
    '兴趣爱好': '#22c55e'
  }
  return colors[type] || '#6b6c7d'
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

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
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
}

.feature-count {
  font-size: 13px;
  color: var(--text-muted);
}

.features-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
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