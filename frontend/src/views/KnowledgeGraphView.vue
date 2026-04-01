<template>
  <div class="knowledge-graph-view">
    <div class="graph-header">
      <h1 class="page-title">
        <span class="title-icon">🔮</span>
        <span class="title-text">用户画像特征图谱</span>
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
      <aside class="left-sidebar">
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

        <div class="legend-card">
          <div class="card-title">图例说明</div>
          <div class="legend-list">
            <div v-for="item in nodeLegendItems" :key="item.id" class="legend-item">
              <div class="legend-dot" :style="{ background: item.color }"></div>
              <span class="legend-name">{{ item.name }}</span>
            </div>
          </div>
        </div>
      </aside>

      <main class="main-content">
        <div class="graph-card">
          <div class="card-header">
            <span class="card-title">🌀 特征图谱</span>
            <div class="graph-controls">
              <el-button size="small" class="mini-btn" @click="zoomIn">+</el-button>
              <el-button size="small" class="mini-btn" @click="zoomOut">-</el-button>
            </div>
          </div>
          <div ref="graphContainer" class="graph-container"></div>
        </div>
      </main>
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

const graphContainer = ref(null)
let chart = null

const featureCount = computed(() => allFeatures.value?.length || 0)

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

const nodeLegendItems = computed(() => {
  const items = [
    { id: 'user', name: '用户', color: NODE_COLORS.user }
  ]
  
  const features = allFeatures.value || []
  const renderedTypes = new Set()
  features.forEach(f => {
    if (f.feature_type && !isFeatureInferred(f) && f.feature_value) {
      renderedTypes.add(f.feature_type)
    }
  })
  
  Array.from(renderedTypes).forEach(type => {
    items.push({ id: `type_${type}`, name: type, color: getTypeColor(type) })
  })
  
  const hasInferred = features.some(f => isFeatureInferred(f) && f.feature_value)
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
  '人际关系': 'linear-gradient(135deg, #06b6d4, #22d3ee)',
  '人际关系Hex': '#06b6d4',
  '家庭关系': 'linear-gradient(135deg, #f97316, #fb923c)',
  '家庭关系Hex': '#f97316',
  '社会角色': 'linear-gradient(135deg, #8b5cf6, #a78bfa)',
  '社会角色Hex': '#8b5cf6',
  '社交特点': 'linear-gradient(135deg, #0ea5e9, #38bdf8)',
  '社交特点Hex': '#0ea5e9',
  '沟通风格': 'linear-gradient(135deg, #6366f1, #818cf8)',
  '沟通风格Hex': '#6366f1',
  '思维模式': 'linear-gradient(135deg, #a855f7, #c084fc)',
  '思维模式Hex': '#a855f7',
  '工作风格': 'linear-gradient(135deg, #3b82f6, #60a5fa)',
  '工作风格Hex': '#3b82f6',
  '情感状态': 'linear-gradient(135deg, #ec4899, #f472b6)',
  '情感状态Hex': '#ec4899',
  '未知': 'linear-gradient(135deg, #6b7280, #9ca3af)',
  '未知Hex': '#6b7280'
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

function buildGraphData() {
  const features = allFeatures.value || []
  const nodes = []
  const links = []
  
  nodes.push({
    id: 'user',
    name: userId.value || '用户',
    category: 0,
    symbolSize: 70,
    draggable: true,
    itemStyle: {
      color: NODE_COLORS.userHex,
      shadowColor: 'rgba(99, 102, 241, 0.5)',
      shadowBlur: 20
    },
    label: {
      show: true,
      position: 'bottom',
      fontSize: 16,
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
  types.forEach((type) => {
    const colorHex = getTypeColorHex(type)
    nodes.push({
      id: `type_${type}`,
      name: type,
      category: 1,
      symbolSize: 55,
      draggable: true,
      itemStyle: {
        color: colorHex,
        shadowColor: `rgba(${hexToRgb(colorHex)}, 0.4)`,
        shadowBlur: 15
      },
      label: {
        show: true,
        position: 'bottom',
        fontSize: 14,
        fontWeight: 600,
        color: '#374151'
      }
    })
    
    links.push({
      source: 'user',
      target: `type_${type}`,
      value: 1,
      lineStyle: {
        width: 5,
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: NODE_COLORS.userHex },
            { offset: 1, color: colorHex }
          ]
        },
        curveness: 0.2,
        opacity: 0.8
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
      symbolSize: 35 + (feature.confidence * 20),
      draggable: true,
      itemStyle: {
        color: color,
        shadowColor: `rgba(${hexToRgb(color)}, 0.4)`,
        shadowBlur: 12,
        opacity: 0.95
      },
      label: {
        show: true,
        position: 'right',
        fontSize: 12,
        color: '#374151',
        formatter: (params) => {
          return params.name.length > 12 ? params.name.slice(0, 12) + '...' : params.name
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
          width: Math.max(2, feature.confidence * 5),
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
      textStyle: { color: '#374151' },
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
      label: { show: true, position: 'right', formatter: '{b}' },
      lineStyle: { color: 'source', curveness: 0.3 },
      force: {
        repulsion: 600,
        gravity: 0.1,
        edgeLength: 180,
        layoutAnimation: true
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 10 },
        label: { fontSize: 14, fontWeight: 'bold' }
      }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', handleResize)
}

function handleResize() {
  if (chart) chart.resize()
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
  if (chart) chart.dispatchAction({ type: 'dataZoom', start: 0, end: 100 })
}

function zoomOut() {
  if (chart) chart.dispatchAction({ type: 'dataZoom', start: 0, end: 100 })
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

watch(allFeatures, async (newFeatures) => {
  if (newFeatures && newFeatures.length > 0) {
    await nextTick()
    renderChart()
  }
}, { deep: true })

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chart) chart.dispose()
})
</script>

<style scoped>
.knowledge-graph-view {
  min-height: calc(100vh - 7rem);
  padding: 1.25rem;
  background: var(--bg-primary);
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.625rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.title-icon {
  font-size: 1.75rem;
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
  grid-template-columns: 18.75rem 1fr;
  gap: 1.25rem;
  height: calc(100vh - 11.25rem);
  min-height: 31.25rem;
}

@media (max-width: 75rem) {
  .graph-content {
    grid-template-columns: 16.25rem 1fr;
  }
}

.left-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.left-sidebar::-webkit-scrollbar {
  width: 0.375rem;
}

.left-sidebar::-webkit-scrollbar-track {
  background: var(--bg-tertiary);
  border-radius: 0.1875rem;
}

.left-sidebar::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 0.1875rem;
}

.user-profile-card,
.feature-types-card,
.legend-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 1rem;
  padding: 1.25rem;
}

.user-avatar {
  margin-bottom: 0.75rem;
}

.avatar-ring {
  width: 4.375rem;
  height: 4.375rem;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 0.25rem;
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
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.user-name {
  text-align: center;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.875rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.625rem;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.75rem 0.5rem;
  background: var(--bg-tertiary);
  border-radius: 0.625rem;
  transition: transform 0.2s ease;
}

.stat-box:hover {
  transform: translateY(-0.125rem);
}

.stat-value {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 0.6875rem;
  color: var(--text-muted);
}

.card-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.875rem;
}

.type-bars {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.type-bar-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
}

.type-name {
  width: 4.375rem;
  font-size: 0.6875rem;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.type-bar {
  flex: 1;
  height: 0.5rem;
  background: var(--bg-tertiary);
  border-radius: 0.25rem;
  overflow: hidden;
}

.type-bar-fill {
  height: 100%;
  border-radius: 0.25rem;
  transition: width 0.6s ease;
}

.type-count {
  width: 1.5rem;
  text-align: right;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-primary);
}

.legend-list {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  transition: transform 0.2s ease;
}

.legend-item:hover {
  transform: translateX(0.25rem);
}

.legend-dot {
  width: 0.875rem;
  height: 0.875rem;
  border-radius: 50%;
}

.legend-name {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.main-content {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.graph-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 1rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.card-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
}

.graph-controls {
  display: flex;
  gap: 0.375rem;
}

.mini-btn {
  width: 1.75rem;
  height: 1.75rem;
  padding: 0;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-weight: 600;
}

.mini-btn:hover {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}

.graph-container {
  flex: 1;
  min-height: 25rem;
}

@media (max-width: 56.25rem) {
  .knowledge-graph-view {
    min-height: auto;
    padding: 0.75rem;
  }
  
  .graph-header {
    margin-bottom: 0.75rem;
  }
  
  .page-title {
    font-size: 1.25rem;
  }
  
  .graph-content {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    height: auto;
    min-height: auto;
  }
  
  .left-sidebar {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(12.5rem, 1fr));
    gap: 0.75rem;
    overflow: visible;
  }
  
  .legend-card {
    display: none;
  }
  
  .main-content {
    min-height: 25rem;
  }
  
  .graph-card {
    height: 100%;
    min-height: 25rem;
  }
  
  .graph-container {
    min-height: 20rem;
  }
}

@media screen and (min-width: 120rem) {
  .knowledge-graph-view {
    max-width: 87.5rem;
    margin: 0 auto;
  }
}
</style>
