<template>
  <div class="profile-view">
    <div class="profile-container">
      <aside class="profile-sidebar">
        <div class="user-card">
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
              <span class="stat-value">{{ confidencePercent }}%</span>
              <span class="stat-label">置信度</span>
            </div>
          </div>
        </div>

        <div class="overview-card">
          <div class="card-title">用户画像概述</div>
          <div class="overview-content">
            <div class="overview-item">
              <span class="overview-label">职业</span>
              <span class="overview-value" :title="getFeatureValueByType('职业') || '未知'">
                {{ getFeatureValueByType('职业') || '未知' }}
              </span>
            </div>
            <div class="overview-item">
              <span class="overview-label">性格</span>
              <span class="overview-value" :title="getMbtiSummary()">
                {{ getMbtiSummary() }}
              </span>
            </div>
            <div class="overview-item">
              <span class="overview-label">兴趣</span>
              <span class="overview-value" :title="getTopInterests()">
                {{ getTopInterests() }}
              </span>
            </div>
            <div class="overview-item">
              <span class="overview-label">生活方式</span>
              <span class="overview-value" :title="getLifestyleSummary()">
                {{ getLifestyleSummary() }}
              </span>
            </div>
          </div>
        </div>
      </aside>

      <main class="profile-main">
        <div class="charts-card">
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
            <el-tab-pane label="特征总览" name="overview">
              <div ref="overviewContainer" class="chart-container"></div>
            </el-tab-pane>
            <el-tab-pane label="特征分布" name="pie">
              <div ref="pieContainer" class="chart-container"></div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <div class="predictions-card">
          <div class="card-header">
            <div class="header-content">
              <span class="card-title">🔮 行为预测</span>
            </div>
            <span class="prediction-count">Top {{ predictions.length }} 预测</span>
          </div>
          <div class="predictions-list">
            <div v-for="(prediction, index) in predictions" :key="prediction.id || index" class="prediction-item" :class="'rank-' + (index + 1)">
              <div class="prediction-rank">{{ index + 1 }}</div>
              <div class="prediction-content">
                <div class="prediction-header">
                  <div class="prediction-tags">
                    <el-tag :type="getCategoryTagType(prediction.category)" size="small">
                      {{ prediction.category }}
                    </el-tag>
                    <el-tag :type="getTimeframeTagType(prediction.timeframe)" size="small">
                      {{ getTimeframeLabel(prediction.timeframe) }}
                    </el-tag>
                  </div>
                  <span class="confidence">{{ (prediction.confidence * 100).toFixed(0) }}% 可能性</span>
                </div>
                <div class="prediction-text">{{ prediction.prediction }}</div>
                <div class="prediction-reasoning">
                  <el-icon><Promotion /></el-icon>
                  {{ prediction.reasoning }}
                </div>
                <div v-if="prediction.observable_signals && prediction.observable_signals.length > 0" class="prediction-signals">
                  <span class="signals-label">可观察信号：</span>
                  <el-tag v-for="(signal, sidx) in prediction.observable_signals" :key="sidx" size="small" effect="plain">
                    {{ signal }}
                  </el-tag>
                </div>
                <div class="prediction-meta">
                  <span class="meta-time">预测于 {{ formatTime(prediction.created_at) }}</span>
                </div>
              </div>
            </div>
            <div v-if="predictions.length === 0 && !generatingPredictions" class="empty-predictions">
              <el-icon :size="48"><MagicStick /></el-icon>
              <p>暂无预测数据</p>
            </div>
            <div v-if="generatingPredictions" class="loading-predictions">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>AI 正在分析预测中...</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, watch, nextTick } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useRoute, onBeforeRouteUpdate } from 'vue-router'
import * as echarts from 'echarts'
import { Refresh, Promotion, Loading, Search, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const store = useProfileStore()
const route = useRoute()

const activeTab = ref('radar')
const profileSummary = ref(null)
const allFeatures = ref([])
const predictions = ref([])
const searchQuery = ref('')
const timelineContainer = ref(null)
const itemsPerLoad = 10
const displayedCount = ref(itemsPerLoad)
const generatingPredictions = ref(false)

const userId = computed(() => store.currentUserId)
const radarContainer = ref(null)
const overviewContainer = ref(null)
const pieContainer = ref(null)

let radarChart = null
let overviewChart = null
let pieChart = null

const confidencePercent = computed(() => {
  if (!allFeatures.value || allFeatures.value.length === 0) return 0
  const sum = allFeatures.value.reduce((acc, f) => acc + (f.confidence || 0), 0)
  const avg = sum / allFeatures.value.length
  return (avg * 100).toFixed(0)
})

const filteredFeatures = computed(() => {
  if (!searchQuery.value) return allFeatures.value
  const query = searchQuery.value.toLowerCase()
  return allFeatures.value.filter(feature => 
    feature.feature_type.toLowerCase().includes(query) ||
    feature.feature_value.toLowerCase().includes(query) ||
    (feature.reasoning && feature.reasoning.toLowerCase().includes(query))
  )
})

const displayedFeatures = computed(() => filteredFeatures.value.slice(0, displayedCount.value))
const hasMore = computed(() => displayedCount.value < filteredFeatures.value.length)

function getFeatureValueByType(type) {
  const feature = allFeatures.value.find(f => f.feature_type === type)
  return feature ? feature.feature_value : null
}

function getMbtiSummary() {
  if (profileSummary.value?.mbti) return profileSummary.value.mbti
  const mbtiFeature = allFeatures.value.find(f => f.feature_type === 'MBTI')
  if (mbtiFeature) {
    const value = mbtiFeature.feature_value
    const match = value.match(/[A-Z]{4}/)
    if (match) return match[0]
    return value.slice(0, 10) + (value.length > 10 ? '...' : '')
  }
  return '未知'
}

function getTopInterests() {
  const interests = allFeatures.value
    .filter(f => f.feature_type === '兴趣爱好')
    .slice(0, 3)
    .map(f => f.feature_value)
  return interests.length ? interests.join('、') : '暂无'
}

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
    else if (activeTab.value === 'overview' && allFeatures.value.length) renderOverviewChart()
    else if (activeTab.value === 'pie' && allFeatures.value.length) renderPieChart()
  })
})

watch(allFeatures, () => {
  nextTick(() => {
    if (profileSummary.value) renderRadarChart()
    if (allFeatures.value.length) {
      renderOverviewChart()
      renderPieChart()
    }
  })
}, { deep: true })

async function loadProfile() {
  try {
    const data = await store.loadProfile()
    profileSummary.value = data.summary
    allFeatures.value = data.features || []
    predictions.value = data.predictions || []
    displayedCount.value = itemsPerLoad
    await nextTick()
    renderRadarChart()
    await generatePredictions(true)
  } catch (e) {
    console.error('Failed to load profile:', e)
  }
}

async function generatePredictions(silent = true, retryCount = 0) {
  if (silent) {
    generatingPredictions.value = false
  } else {
    generatingPredictions.value = true
  }
  
  try {
    const response = await fetch(`/api/profile/${userId.value}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force_refresh: false })
    })
    
    if (response.ok) {
      const result = await response.json()
      predictions.value = result.predictions || []
      if (!silent) {
        if (result.cached) {
          ElMessage.success('已加载缓存的预测结果')
        } else {
          ElMessage.success('AI 预测已生成')
        }
      }
    } else if (response.status >= 500 && retryCount < 2) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      await generatePredictions(silent, retryCount + 1)
    } else if (!silent) {
      ElMessage.error('生成预测失败')
    }
  } catch (e) {
    if (!silent) {
      console.warn('预测生成跳过:', e.message)
    }
  } finally {
    generatingPredictions.value = false
  }
}

async function refreshProfile() {
  try {
    const analyzeResponse = await fetch(`/api/profile/${userId.value}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
    
    if (analyzeResponse.ok) {
      ElMessage.success('已触发用户画像分析任务，后台处理中...')
    }
    
    await loadProfile()
    ElMessage.success('用户画像已更新')
  } catch (e) {
    console.error('刷新失败:', e)
    ElMessage.error('刷新失败：' + e.message)
  }
}

function renderRadarChart() {
  if (!radarContainer.value) return
  if (radarChart) radarChart.dispose()
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
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: 'var(--border-light)',
      borderWidth: 1,
      textStyle: { color: 'var(--text-primary)', fontSize: 14 }
    },
    radar: {
      indicator: indicators,
      radius: '65%',
      axisName: {
        color: '#0f172a',
        fontSize: 14,
        fontWeight: 600,
        padding: [10, 10, 10, 10]
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(99, 102, 241, 0.03)', 'rgba(99, 102, 241, 0.08)']
        }
      },
      splitLine: { lineStyle: { color: 'var(--border-light)', width: 1 } },
      axisLine: { lineStyle: { color: 'var(--border-medium)', width: 1 } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '大五人格',
        areaStyle: { color: 'rgba(99, 102, 241, 0.25)' },
        lineStyle: { color: '#6366f1', width: 2 },
        itemStyle: { color: '#6366f1', borderWidth: 2 },
        label: {
          show: true,
          color: '#0f172a',
          fontSize: 12,
          fontWeight: 600,
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          padding: [2, 6, 2, 6],
          borderRadius: 4
        }
      }]
    }]
  }

  radarChart.setOption(option)
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '99, 102, 241'
}

function renderOverviewChart() {
  if (!overviewContainer.value) return
  if (overviewChart) overviewChart.dispose()
  overviewChart = echarts.init(overviewContainer.value)

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
    overviewChart.setOption(option)
    return
  }

  const typeStats = {}
  displayFeatures.forEach(f => {
    if (!typeStats[f.feature_type]) {
      typeStats[f.feature_type] = {
        count: 0,
        totalConfidence: 0,
        colors: getFeatureColor(f.feature_type)
      }
    }
    typeStats[f.feature_type].count++
    typeStats[f.feature_type].totalConfidence += f.confidence
  })

  Object.keys(typeStats).forEach(type => {
    typeStats[type].avgConfidence = typeStats[type].totalConfidence / typeStats[type].count
  })

  const nodes = [{
    id: 'user',
    name: userId.value,
    category: 0,
    symbolSize: 70,
    itemStyle: {
      color: '#6366f1',
      shadowColor: 'rgba(99, 102, 241, 0.4)',
      shadowBlur: 15
    },
    label: {
      show: true,
      position: 'bottom',
      fontSize: 14,
      fontWeight: 'bold',
      color: 'var(--text-primary)'
    }
  }]

  const categories = Object.keys(typeStats)
  categories.forEach((type, idx) => {
    const stats = typeStats[type]
    const size = 35 + (stats.count * 2)
    
    nodes.push({
      id: `type_${type}`,
      name: type,
      category: 1,
      symbolSize: Math.min(size, 60),
      itemStyle: {
        color: stats.colors,
        shadowColor: `rgba(${hexToRgb(stats.colors)}, 0.35)`,
        shadowBlur: 12
      },
      label: {
        show: true,
        position: 'bottom',
        fontSize: 12,
        fontWeight: 600,
        color: 'var(--text-secondary)',
        formatter: (params) => {
          return `{name|${params.name}}\n{count|${stats.count}个特征}\n{conf|${(stats.avgConfidence * 100).toFixed(0)}%}`
        },
        rich: {
          name: { fontSize: 12, fontWeight: 600, lineHeight: 18 },
          count: { fontSize: 10, color: 'var(--text-muted)', lineHeight: 14 },
          conf: { fontSize: 10, color: '#22c55e', fontWeight: 600, lineHeight: 14 }
        }
      }
    })
  })

  const links = categories.map(type => ({
    source: 'user',
    target: `type_${type}`,
    value: typeStats[type].avgConfidence,
    lineStyle: {
      width: 2 + (typeStats[type].avgConfidence * 2),
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [
          { offset: 0, color: '#6366f1' },
          { offset: 1, color: typeStats[type].colors }
        ]
      },
      curveness: 0.2,
      opacity: 0.7
    }
  }))

  const option = {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1500,
    animationEasing: 'cubicOut',
    tooltip: {
      show: true,
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: 'var(--border-light)',
      borderWidth: 1,
      textStyle: { color: 'var(--text-primary)' },
      formatter: (params) => {
        if (params.dataType === 'edge') {
          return `<div style="padding: 8px;"><div style="color: #6366f1; font-weight: 600; margin-bottom: 8px;">特征类别</div><div>平均置信度：${((params.data.value || 0) * 100).toFixed(0)}%</div></div>`
        }
        if (params.name === userId.value) {
          return `<div style="padding: 8px;"><div style="color: #6366f1; font-weight: 600; font-size: 14px; margin-bottom: 8px;">${params.name}</div><div>特征类型：${categories.length} 种</div><div>特征总数：${displayFeatures.length} 个</div></div>`
        }
        const stats = typeStats[params.name]
        return `<div style="padding: 8px;"><div style="color: ${stats.colors}; font-weight: 600; font-size: 14px; margin-bottom: 8px;">${params.name}</div><div>特征数量：<span style="color: #22c55e; font-weight: 600;">${stats.count} 个</span></div><div>平均置信度：<span style="color: #22c55e; font-weight: 600;">${(stats.avgConfidence * 100).toFixed(0)}%</span></div></div>`
      }
    },
    legend: { show: false },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      label: { show: true, position: 'bottom' },
      categories: [
        { name: '用户' },
        { name: '特征类型' }
      ],
      nodes: nodes,
      links: links,
      lineStyle: { curveness: 0.2 },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 6 }
      },
      force: {
        repulsion: 500,
        gravity: 0.1,
        edgeLength: 150
      }
    }]
  }

  overviewChart.setOption(option)
}

function renderPieChart() {
  if (!pieContainer.value) return
  if (pieChart) pieChart.dispose()
  pieChart = echarts.init(pieContainer.value)

  const typeCount = {}
  const typeConfidence = {}
  allFeatures.value.forEach(f => {
    if (!typeCount[f.feature_type]) {
      typeCount[f.feature_type] = 0
      typeConfidence[f.feature_type] = 0
    }
    typeCount[f.feature_type]++
    typeConfidence[f.feature_type] += f.confidence
  })

  Object.keys(typeCount).forEach(type => {
    typeConfidence[type] = typeConfidence[type] / typeCount[type]
  })

  const sortedData = Object.entries(typeCount)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value], index) => ({
      name,
      value,
      confidence: typeConfidence[name],
      itemStyle: { color: getFeatureColor(name) }
    }))

  const option = {
    backgroundColor: 'transparent',
    animation: true,
    animationDuration: 1500,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: 'var(--border-light)',
      borderWidth: 1,
      textStyle: { color: 'var(--text-primary)' },
      formatter: (params) => {
        const data = sortedData[params[0].dataIndex]
        return `<div style="padding: 8px;"><div style="color: ${data.itemStyle.color}; font-weight: 600; font-size: 14px; margin-bottom: 8px;">${data.name}</div><div>特征数量：<span style="color: #6366f1; font-weight: 600;">${data.value} 个</span></div><div>平均置信度：<span style="color: #22c55e; font-weight: 600;">${(data.confidence * 100).toFixed(0)}%</span></div><div>占比：<span style="color: #f59e0b; font-weight: 600;">${((data.value / allFeatures.value.length) * 100).toFixed(1)}%</span></div></div>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: sortedData.map(item => item.name),
      axisLabel: {
        interval: 0,
        rotate: 30,
        fontSize: 11,
        color: 'var(--text-secondary)',
        fontWeight: 500
      },
      axisLine: { lineStyle: { color: 'var(--border-light)' } },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      name: '特征数量',
      nameTextStyle: { color: 'var(--text-muted)', fontSize: 12 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: {
        lineStyle: {
          color: 'var(--border-light)',
          type: 'dashed',
          opacity: 0.5
        }
      },
      axisLabel: {
        color: 'var(--text-muted)',
        fontSize: 11
      }
    },
    series: [{
      type: 'bar',
      data: sortedData,
      barWidth: '50%',
      itemStyle: {
        borderRadius: [6, 6, 0, 0],
        shadowColor: 'rgba(0, 0, 0, 0.08)',
        shadowBlur: 8,
        shadowOffsetY: 3
      },
      label: {
        show: true,
        position: 'top',
        fontSize: 11,
        fontWeight: 600,
        color: 'var(--text-primary)',
        formatter: (params) => {
          return `{count|${params.value}}{percent|\n${((params.value / allFeatures.value.length) * 100).toFixed(0)}%}`
        },
        rich: {
          count: { fontSize: 12, fontWeight: 600, lineHeight: 14 },
          percent: { fontSize: 10, color: 'var(--text-muted)', lineHeight: 12 }
        }
      },
      emphasis: {
        itemStyle: {
          shadowColor: 'rgba(0, 0, 0, 0.15)',
          shadowBlur: 12,
          shadowOffsetY: 5
        },
        label: { fontSize: 12, fontWeight: 'bold' }
      }
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
  if (predefinedColors[type]) return predefinedColors[type]
  const colors = ['#8b5cf6', '#2196f3', '#f59e0b', '#ef4444', '#22c55e', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#a855f7']
  let hash = 0
  for (let i = 0; i < type.length; i++) {
    hash = type.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
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

function getCategoryTagType(category) {
  const types = {
    '行为': 'warning',
    '想法': 'primary',
    '情感': 'danger',
    '决策': 'success',
    '其他': 'info'
  }
  return types[category] || 'info'
}

function getTimeframeTagType(timeframe) {
  const types = {
    '短期': 'success',
    '中期': 'warning',
    '长期': 'danger'
  }
  return types[timeframe] || 'info'
}

function getTimeframeLabel(timeframe) {
  const labels = {
    '短期': '1-7 天',
    '中期': '1-4 周',
    '长期': '1-3 月'
  }
  return labels[timeframe] || timeframe
}
</script>

<style scoped>
.profile-view {
  height: 100%;
}

.profile-container {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
  align-items: start;
}

.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
  position: sticky;
  top: 0;
}

.user-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  padding: 28px 24px;
  text-align: center;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.user-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.user-avatar {
  margin-bottom: 16px;
}

.avatar-ring {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  padding: 3px;
  margin: 0 auto;
}

.avatar-inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 700;
  color: var(--color-primary);
}

.user-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.3px;
}

.user-badge {
  margin-bottom: 20px;
}

.mbti-badge {
  display: inline-block;
  padding: 6px 16px;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  color: white;
  letter-spacing: 1px;
}

.user-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px 0;
  border-top: 1px solid var(--border-light);
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 4px;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--border-light);
}

.overview-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
}

.overview-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  letter-spacing: -0.2px;
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
  padding: 12px 14px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.overview-item:hover {
  background: var(--bg-tertiary);
}

.overview-label {
  font-size: 13px;
  color: var(--text-secondary);
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

.profile-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.charts-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  height: 32px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}

.refresh-btn {
  color: var(--text-muted);
  transition: all var(--transition-fast);
}

.refresh-btn:hover {
  color: var(--color-primary);
}

.profile-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-light);
}

.profile-tabs :deep(.el-tabs__item) {
  color: var(--text-secondary);
  font-weight: 500;
}

.profile-tabs :deep(.el-tabs__item.is-active) {
  color: var(--color-primary);
  font-weight: 600;
}

.profile-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--color-primary);
  height: 2px;
}

.chart-container {
  height: 360px;
}

.predictions-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
}

.prediction-count {
  font-size: 13px;
  color: var(--text-muted);
}

.predictions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

.predictions-list::-webkit-scrollbar {
  width: 6px;
}

.predictions-list::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 3px;
}

.predictions-list::-webkit-scrollbar-thumb {
  background: var(--border-light);
  border-radius: 3px;
}

.prediction-item {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-light);
  transition: all var(--transition-base);
  animation: slideIn 0.4s ease both;
}

.prediction-item:hover {
  border-color: var(--color-primary);
  transform: translateX(4px);
  box-shadow: var(--shadow-md);
}

.prediction-item.rank-1 {
  border-left: 4px solid #f59e0b;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.05), var(--bg-secondary));
}

.prediction-item.rank-2 {
  border-left: 4px solid #9ca3af;
  background: linear-gradient(135deg, rgba(156, 163, 175, 0.05), var(--bg-secondary));
}

.prediction-item.rank-3 {
  border-left: 4px solid #b45309;
  background: linear-gradient(135deg, rgba(180, 83, 9, 0.05), var(--bg-secondary));
}

.prediction-rank {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
}

.prediction-item.rank-1 .prediction-rank {
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
}

.prediction-item.rank-2 .prediction-rank {
  background: linear-gradient(135deg, #9ca3af, #6b7280);
}

.prediction-item.rank-3 .prediction-rank {
  background: linear-gradient(135deg, #b45309, #d97706);
}

.prediction-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.prediction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.prediction-tags {
  display: flex;
  gap: 8px;
  align-items: center;
}

.prediction-text {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.5;
}

.prediction-reasoning {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
  background: white;
  padding: 12px 14px;
  border-radius: var(--radius-md);
}

.prediction-reasoning .el-icon {
  color: #f59e0b;
  margin-top: 2px;
  flex-shrink: 0;
}

.prediction-signals {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.signals-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.prediction-meta {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.meta-time {
  font-size: 12px;
  color: var(--text-muted);
}

.empty-predictions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.empty-predictions p {
  margin-top: 12px;
  font-size: 14px;
}

.loading-predictions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 20px;
  color: var(--text-muted);
  font-size: 14px;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@media (max-width: 1200px) {
  .profile-container {
    grid-template-columns: 1fr;
  }
  
  .profile-sidebar {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 20px;
    position: relative;
    top: auto;
  }
}

@media (max-width: 768px) {
  .profile-sidebar {
    grid-template-columns: 1fr;
  }
  
  .user-card,
  .overview-card,
  .charts-card,
  .predictions-card {
    padding: 20px;
  }
  
  .chart-container {
    height: 300px;
  }
  
  .prediction-item {
    padding: 16px;
    flex-direction: column;
    gap: 12px;
  }
  
  .prediction-rank {
    width: 32px;
    height: 32px;
    font-size: 12px;
  }
}

@media (max-width: 480px) {
  .user-card,
  .overview-card,
  .charts-card,
  .predictions-card {
    padding: 16px;
    border-radius: var(--radius-lg);
  }
  
  .avatar-ring {
    width: 72px;
    height: 72px;
  }
  
  .avatar-inner {
    font-size: 26px;
  }
  
  .user-name {
    font-size: 18px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .chart-container {
    height: 260px;
  }
  
  .predictions-list {
    max-height: 500px;
  }
}
</style>
