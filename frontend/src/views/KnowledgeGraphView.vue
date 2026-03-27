<template>
  <div class="knowledge-graph-view">
    <div class="graph-header">
      <h1 class="page-title">
        <span class="title-icon">🔮</span>
        <span class="title-text">用户画像知识图谱</span>
      </h1>
      <div class="header-actions">
        <el-button class="action-btn" @click="refreshGraph">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button class="action-btn" @click="fitView">
          <el-icon><FullScreen /></el-icon>
          适应视图
        </el-button>
      </div>
    </div>

    <div class="graph-content">
      <aside class="graph-sidebar">
        <div class="user-profile-card">
          <div class="user-avatar">
            <div class="avatar-ring">
              <div class="avatar-inner">
                {{ (userId?.charAt(0) || 'U').toUpperCase() }}
              </div>
            </div>
          </div>
          <h2 class="user-name">{{ userId || '用户画像' }}</h2>
          
          <div class="stats-grid">
            <div class="stat-box">
              <div class="stat-value">{{ featureCount }}</div>
              <div class="stat-label">特征总数</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">{{ typeCount }}</div>
              <div class="stat-label">特征类型</div>
            </div>
          </div>
        </div>

        <div class="feature-types-card">
          <div class="card-title">特征类型分布</div>
          <div class="type-bars">
            <div v-for="(count, type) in typeDistribution" :key="type" class="type-bar-item">
              <div class="type-name">{{ type }}</div>
              <div class="type-bar">
                <div 
                  class="type-bar-fill" 
                  :style="{ 
                    width: (count / featureCount * 100) + '%',
                    background: getTypeColor(type)
                  }"
                ></div>
              </div>
              <div class="type-count">{{ count }}</div>
            </div>
          </div>
        </div>

      </aside>

      <main class="graph-main">
        <div class="graph-card">
          <div class="card-header">
            <span class="card-title">🌀 知识图谱</span>
            <div class="graph-controls">
              <el-button size="small" class="mini-btn" @click="zoomIn">+</el-button>
              <el-button size="small" class="mini-btn" @click="zoomOut">-</el-button>
            </div>
          </div>
          <div ref="graphContainer" class="graph-container"></div>
        </div>
      </main>

      <aside class="features-sidebar">
        <div class="features-detail-card">
          <div class="card-header">
            <span class="card-title">📋 详细特征</span>
            <span class="feature-count">{{ filteredFeatures.length }} 个</span>
          </div>
          <el-input
            v-model="searchQuery"
            placeholder="搜索特征..."
            clearable
            prefix-icon="Search"
            class="search-input"
            size="small"
          />
          <div class="features-list">
            <div
              v-for="(feature, index) in filteredFeatures"
              :key="index"
              class="feature-item"
              :style="{ animationDelay: (index * 0.03) + 's' }"
            >
              <div class="feature-type-badge" :style="{ background: getFeatureDisplayType(feature).color }">
                {{ getFeatureDisplayType(feature).label }}
              </div>
              <div class="feature-content">
                <div class="feature-value">{{ feature.feature_value }}</div>
                <div class="feature-meta">
                  <span class="feature-confidence">置信度: {{ (feature.confidence * 100).toFixed(0) }}%</span>
                  <span class="feature-verification" v-if="feature.verification_count > 0">
                    已证实 {{ feature.verification_count }} 次
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useProfileStore } from '@/stores/profile'
import * as echarts from 'echarts'
import { Refresh, FullScreen } from '@element-plus/icons-vue'

const store = useProfileStore()
const userId = computed(() => store.user_id)
const allFeatures = computed(() => store.features)

const searchQuery = ref('')
const graphContainer = ref(null)
let chart = null

const featureCount = computed(() => allFeatures.value?.length || 0)

const verifiedCount = computed(() => {
  if (!allFeatures.value) return 0
  return allFeatures.value.filter(f => f.verification_count > 0).length
})

const inferredCount = computed(() => {
  if (!allFeatures.value) return 0
  return allFeatures.value.filter(f => isFeatureInferred(f)).length
})

const typeCount = computed(() => {
  if (!allFeatures.value) return 0
  return [...new Set(allFeatures.value.map(f => f.feature_type))].length
})

const typeDistribution = computed(() => {
  const dist = {}
  if (!allFeatures.value) return dist
  allFeatures.value.forEach(f => {
    dist[f.feature_type] = (dist[f.feature_type] || 0) + 1
  })
  return dist
})

const filteredFeatures = computed(() => {
  if (!allFeatures.value) return []
  if (!searchQuery.value) return allFeatures.value
  const query = searchQuery.value.toLowerCase()
  return allFeatures.value.filter(f => 
    f.feature_type?.toLowerCase().includes(query) ||
    f.feature_value?.toLowerCase().includes(query)
  )
})

const nodeLegendItems = computed(() => {
  const items = [
    { id: 'user', name: '用户', color: NODE_COLORS.user }
  ]
  
  const types = new Set()
  ;(allFeatures.value || []).forEach(f => {
    if (f.feature_type && !isFeatureInferred(f)) {
      types.add(f.feature_type)
    }
  })
  
  Array.from(types).forEach(type => {
    items.push({ id: `type_${type}`, name: type, color: getTypeColor(type) })
  })
  
  const hasInferred = (allFeatures.value || []).some(f => isFeatureInferred(f))
  if (hasInferred) {
    items.push({ id: 'inferred', name: '推断特征', color: NODE_COLORS.inferred })
  }
  
  return items
})

const NODE_COLORS = {
  user: 'linear-gradient(135deg, #6366f1, #4f46e5)',
  userHex: '#6366f1',
  feature: 'linear-gradient(135deg, #22c55e, #16a34a)',
  featureHex: '#22c55e',
  inferred: 'linear-gradient(135deg, #f59e0b, #d97706)',
  inferredHex: '#f59e0b'
}

const TYPE_COLORS = {
  'MBTI': 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
  'MBTIHex': '#8b5cf6',
  '大五人格': 'linear-gradient(135deg, #2196f3, #64b5f6)',
  '大五人格Hex': '#2196f3',
  '行为习惯': 'linear-gradient(135deg, #f59e0b, #fbbf24)',
  '行为习惯Hex': '#f59e0b',
  '潜在想法': 'linear-gradient(135deg, #ef4444, #f87171)',
  '潜在想法Hex': '#ef4444',
  '兴趣爱好': 'linear-gradient(135deg, #22c55e, #4ade80)',
  '兴趣爱好Hex': '#22c55e',
  '用户信息': 'linear-gradient(135deg, #ec4899, #f472b6)',
  '用户信息Hex': '#ec4899',
  '个人信息': 'linear-gradient(135deg, #ec4899, #f472b6)',
  '个人信息Hex': '#ec4899',
  '价值观': 'linear-gradient(135deg, #14b8a6, #2dd4bf)',
  '价值观Hex': '#14b8a6',
  '个人': 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
  '个人Hex': '#0ea5e9',
  '推断': 'linear-gradient(135deg, #f59e0b, #fbbf24)',
  '推断Hex': '#f59e0b',
  '推断特征': 'linear-gradient(135deg, #f59e0b, #fbbf24)',
  '推断特征Hex': '#f59e0b',
  '未知': 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
  '未知Hex': '#0ea5e9'
}

function getTypeColor(type) {
  return TYPE_COLORS[type] || TYPE_COLORS['未知']
}

function getTypeColorHex(type) {
  return TYPE_COLORS[`${type}Hex`] || TYPE_COLORS['未知Hex']
}

function isFeatureInferred(feature) {
  return feature.feature_type === '推断' || feature.feature_type === '推断特征'
}

function formatTypeLabel(type) {
  const labelMap = {
    'MBTI': 'MBTI',
    '大五人格': '大五',
    '行为习惯': '习惯',
    '潜在想法': '想法',
    '兴趣爱好': '爱好',
    '用户信息': '信息',
    '价值观': '价值',
    '个人': '个人',
    '推断': '推断'
  }
  return labelMap[type] || type?.slice(0, 2) || '未知'
}

function getFeatureDisplayType(feature) {
  if (isFeatureInferred(feature)) {
    return { type: '推断', label: '推断', color: NODE_COLORS.inferred }
  }
  return { type: feature.feature_type, label: formatTypeLabel(feature.feature_type), color: getTypeColor(feature.feature_type) }
}

function buildGraphData() {
  const features = allFeatures.value || []
  const nodes = []
  const links = []
  
  nodes.push({
    id: 'user',
    name: userId.value || '用户',
    category: 0,
    symbolSize: 65,
    draggable: true,
    itemStyle: {
      color: NODE_COLORS.userHex,
      shadowColor: 'rgba(99, 102, 241, 0.5)',
      shadowBlur: 15
    },
    label: {
      show: true,
      position: 'bottom',
      fontSize: 15,
      fontWeight: 'bold',
      color: '#1f2937'
    }
  })
  
  const allFeatureTypes = new Set()
  features.forEach(f => {
    if (f.feature_type && !isFeatureInferred(f)) {
      allFeatureTypes.add(f.feature_type)
    }
  })
  
  const types = Array.from(allFeatureTypes)
  types.forEach((type, idx) => {
    const colorHex = getTypeColorHex(type)
    nodes.push({
      id: `type_${type}`,
      name: type,
      category: 1,
      symbolSize: 50,
      draggable: true,
      itemStyle: {
        color: colorHex,
        shadowColor: `rgba(${hexToRgb(colorHex)}, 0.4)`,
        shadowBlur: 12
      },
      label: {
        show: true,
        position: 'bottom',
        fontSize: 13,
        fontWeight: 600,
        color: '#374151'
      }
    })
    
    links.push({
      source: 'user',
      target: `type_${type}`,
      value: 1,
      lineStyle: {
        width: 4,
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 1,
          y2: 0,
          colorStops: [{
            offset: 0, color: NODE_COLORS.userHex
          }, {
            offset: 1, color: colorHex
          }]
        },
        curveness: 0.2,
        opacity: 0.7
      }
    })
  })
  
  features.forEach((feature, idx) => {
    const isInferred = isFeatureInferred(feature)
    let featureType = feature.feature_type
    
    if (isInferred) {
      featureType = types.length > 0 ? types[0] : null
    }
    
    const typeColorHex = featureType ? getTypeColorHex(featureType) : NODE_COLORS.inferredHex
    const color = isInferred ? NODE_COLORS.inferredHex : typeColorHex
    
    nodes.push({
      id: `feature_${idx}`,
      name: feature.feature_value,
      category: isInferred ? 3 : 2,
      symbolSize: 32 + (feature.confidence * 18),
      draggable: true,
      itemStyle: {
        color: color,
        shadowColor: `rgba(${hexToRgb(color)}, 0.4)`,
        shadowBlur: 10,
        opacity: 0.95
      },
      label: {
        show: true,
        position: 'right',
        fontSize: 11,
        color: '#374151',
        formatter: (params) => {
          return params.name.length > 10 ? params.name.slice(0, 10) + '...' : params.name
        }
      },
      value: feature.confidence
    })
    
    if (featureType && types.includes(featureType)) {
      links.push({
        source: `type_${featureType}`,
        target: `feature_${idx}`,
        value: feature.confidence,
        lineStyle: {
          width: Math.max(1, feature.confidence * 4),
          color: color,
          curveness: 0.3,
          type: isInferred ? 'dashed' : 'solid',
          opacity: isInferred ? 0.6 : 0.8
        }
      })
    }
  })
  
  return { nodes, links }
}

function extractHexFromGradient(gradient) {
  const match = gradient?.match(/#[a-f0-9]{6}/i)
  return match ? match[0] : '#6366f1'
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result 
    ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
    : '99, 102, 241'
}

function renderChart() {
  if (!graphContainer.value) return
  
  if (chart) {
    chart.dispose()
  }
  
  chart = echarts.init(graphContainer.value)
  
  const { nodes, links } = buildGraphData()
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      show: true,
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151'
      },
      formatter: (params) => {
        if (params.dataType === 'edge') {
          return `<div style="padding: 8px;">
            <div style="color: #6366f1; font-weight: 600; margin-bottom: 8px;">连接关系</div>
            <div>${params.data.source} → ${params.data.target}</div>
            <div style="color: #6b7280; margin-top: 4px;">置信度: ${((params.data.value || 0) * 100).toFixed(0)}%</div>
          </div>`
        }
        let content = `<div style="padding: 8px;">`
        content += `<div style="color: #6366f1; font-weight: 600; font-size: 14px; margin-bottom: 8px;">${params.name}</div>`
        if (params.data.value !== undefined) {
          content += `<div style="color: #6b7280;">置信度: <span style="color: #22c55e; font-weight: 600;">${(params.data.value * 100).toFixed(0)}%</span></div>`
        }
        content += '</div>'
        return content
      }
    },
    animationDurationUpdate: 2000,
    animationEasingUpdate: 'cubicOut',
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: links,
      categories: [
        { name: '用户' },
        { name: '特征类型' },
        { name: '特征值' },
        { name: '推断特征' }
      ],
      roam: true,
      label: {
        show: true,
        position: 'right',
        formatter: '{b}'
      },
      lineStyle: {
        color: 'source',
        curveness: 0.3
      },
      force: {
        repulsion: 500,
        gravity: 0.1,
        edgeLength: 160,
        layoutAnimation: true
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 8
        },
        label: {
          fontSize: 14,
          fontWeight: 'bold'
        }
      }
    }]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', handleResize)
}

function handleResize() {
  if (chart) {
    chart.resize()
  }
}

function fitView() {
  if (chart) {
    const option = chart.getOption()
    if (option.series?.[0]) {
      option.series[0].roam = false
      chart.setOption(option)
      setTimeout(() => {
        option.series[0].roam = true
        chart.setOption(option)
      }, 300)
    }
  }
}

function zoomIn() {
  if (chart) {
    chart.dispatchAction({
      type: 'dataZoom',
      start: 0,
      end: 100
    })
  }
}

function zoomOut() {
  if (chart) {
    chart.dispatchAction({
      type: 'dataZoom',
      start: 0,
      end: 100
    })
  }
}

async function refreshGraph() {
  try {
    await store.loadProfile()
    await nextTick()
    renderChart()
  } catch (e) {
    console.error('Failed to refresh:', e)
  }
}

onMounted(async () => {
  await store.loadProfile()
  await nextTick()
  renderChart()
})

// 监听特征数据变化，重新渲染图表
watch(allFeatures, async (newFeatures) => {
  if (newFeatures && newFeatures.length > 0) {
    await nextTick()
    renderChart()
  }
}, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) {
    chart.dispose()
  }
})
</script>

<style scoped>
.knowledge-graph-view {
  min-height: calc(100vh - 112px);
  padding: 20px;
  background: var(--bg-primary);
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.title-icon {
  font-size: 28px;
}

.action-btn {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}

.graph-content {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 20px;
  height: calc(100vh - 180px);
  min-height: 500px;
}

@media (max-width: 1400px) {
  .graph-content {
    grid-template-columns: 260px 1fr 280px;
  }
}

@media (max-width: 1200px) {
  .graph-content {
    grid-template-columns: 250px 1fr;
  }
  
  .features-sidebar {
    display: none;
  }
}

@media (max-width: 900px) {
  .graph-content {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto 1fr;
    height: auto;
    min-height: auto;
  }
  
  .graph-sidebar {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
    overflow-y: visible;
  }
  
  .features-sidebar {
    display: block;
    max-height: 400px;
  }
}

@media (max-width: 600px) {
  .knowledge-graph-view {
    padding: 12px;
  }
  
  .graph-content {
    gap: 12px;
  }
  
  .graph-sidebar {
    grid-template-columns: 1fr;
  }
  
  .page-title {
    font-size: 20px;
  }
}

.graph-sidebar,
.features-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  padding-right: 8px;
}

.graph-sidebar::-webkit-scrollbar,
.features-sidebar::-webkit-scrollbar {
  width: 6px;
}

.graph-sidebar::-webkit-scrollbar-track,
.features-sidebar::-webkit-scrollbar-track {
  background: var(--bg-tertiary);
  border-radius: 3px;
}

.graph-sidebar::-webkit-scrollbar-thumb,
.features-sidebar::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.user-profile-card,
.feature-types-card,
.legend-card,
.features-detail-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
}

.user-avatar {
  margin-bottom: 16px;
}

.avatar-ring {
  width: 90px;
  height: 90px;
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
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}

.user-name {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: var(--bg-tertiary);
  border-radius: 10px;
  transition: transform 0.2s ease;
}

.stat-box:hover {
  transform: translateY(-2px);
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-value.inferred {
  color: #f59e0b;
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 14px;
}

.type-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.type-bar-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.type-name {
  width: 70px;
  font-size: 11px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.type-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.type-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.type-count {
  width: 24px;
  text-align: right;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.legend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  transition: transform 0.2s ease;
}

.legend-item:hover {
  transform: translateX(4px);
}

.legend-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
}

.legend-dot.user {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
}

.legend-dot.type {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.legend-dot.feature {
  background: linear-gradient(135deg, #22c55e, #16a34a);
}

.legend-dot.inferred {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.legend-text {
  font-size: 13px;
  color: var(--text-secondary);
}

.graph-main {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.graph-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.graph-tip {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 10px;
  padding: 6px 12px;
  background: var(--bg-tertiary);
  border-radius: 6px;
  border-left: 3px solid var(--accent-color);
}

.graph-controls {
  display: flex;
  gap: 6px;
}

.mini-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 6px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-weight: bold;
  font-size: 14px;
}

.mini-btn:hover {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}

.graph-container {
  width: 100%;
  flex: 1;
  min-height: 500px;
  border-radius: 12px;
  background: var(--bg-tertiary);
}

.features-detail-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.feature-count {
  font-size: 12px;
  color: var(--text-muted);
}

.search-input {
  margin-bottom: 12px;
}

.search-input :deep(.el-input__wrapper) {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  box-shadow: none;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: var(--accent-color);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  flex: 1;
  padding-right: 4px;
}

.features-list::-webkit-scrollbar {
  width: 6px;
}

.features-list::-webkit-scrollbar-track {
  background: var(--bg-tertiary);
  border-radius: 3px;
}

.features-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  animation: fadeInUp 0.4s ease both;
  transition: all 0.2s ease;
}

.feature-item:hover {
  border-color: var(--accent-color);
  transform: translateX(3px);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.feature-type-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 600;
  color: white;
  width: fit-content;
}

.feature-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.feature-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.4;
}

.feature-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.feature-meta span {
  font-size: 10px;
  color: var(--text-muted);
  background: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: 4px;
}

.feature-confidence {
  color: #22c55e !important;
}

.feature-verification {
  color: #3b82f6 !important;
}
</style>
