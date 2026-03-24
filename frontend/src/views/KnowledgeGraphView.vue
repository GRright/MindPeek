<template>
  <div class="knowledge-graph-view">
    <div class="graph-main">
      <div class="graph-header">
        <div class="header-left">
          <el-icon :size="20"><Connection /></el-icon>
          <span class="header-title">知识图谱</span>
        </div>
        <div class="header-actions">
          <el-button size="small" @click="loadGraph">刷新</el-button>
        </div>
      </div>

      <div class="graph-container" ref="graphContainer">
        <div v-if="!graphData" class="empty-state">
          <div class="empty-icon">
            <el-icon :size="64"><Share /></el-icon>
          </div>
          <p class="empty-title">知识图谱</p>
          <p class="empty-desc">正在加载用户特征关系网络...</p>
        </div>
        <div v-else ref="networkContainer" class="network-container"></div>
      </div>
    </div>

    <aside class="graph-sidebar">
      <div class="stats-card">
        <div class="card-title">节点统计</div>
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-value">{{ graphData?.nodes?.length || 0 }}</span>
            <span class="stat-label">总节点数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ graphData?.edges?.length || 0 }}</span>
            <span class="stat-label">总边数</span>
          </div>
        </div>
      </div>

      <div class="types-card">
        <div class="card-title">节点图例</div>
        <div class="types-list">
          <div v-for="(item, index) in legendItems" :key="index" class="type-item">
            <div class="type-dot" :style="{ background: item.color }"></div>
            <span class="type-name">{{ item.label }}</span>
          </div>
        </div>
      </div>

      <div class="relations-card">
        <div class="card-title">关系说明</div>
        <div class="relations-list">
          <div class="relation-item">
            <div class="relation-line solid"></div>
            <span class="relation-name">has_feature_type</span>
            <span class="relation-desc">用户拥有的特征类型</span>
          </div>
          <div class="relation-item">
            <div class="relation-line dashed"></div>
            <span class="relation-name">is_a</span>
            <span class="relation-desc">属于该类型的特征值</span>
          </div>
          <div class="relation-item">
            <div class="relation-line dashed" style="border-color: #f59e0b;"></div>
            <span class="relation-name">implies</span>
            <span class="relation-desc">推理得到的关联</span>
          </div>
        </div>
      </div>

      <div class="features-card" v-if="featureValues.length > 0">
        <div class="card-title">用户特征</div>
        <div class="features-list">
          <div
            v-for="(feature, index) in featureValues"
            :key="index"
            class="feature-item"
          >
            <div class="feature-type">{{ feature.type }}</div>
            <div class="feature-value">{{ feature.value }}</div>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { Network } from 'vis-network/standalone'
import { Connection, Share } from '@element-plus/icons-vue'

const store = useProfileStore()

const loading = ref(false)
const graphData = ref(null)
const graphContainer = ref(null)
const networkContainer = ref(null)
let network = null

const nodeTypeStats = computed(() => {
  if (!graphData.value?.nodes) return {}
  const stats = {}
  graphData.value.nodes.forEach(node => {
    const type = node.type || 'unknown'
    stats[type] = (stats[type] || 0) + 1
  })
  return stats
})

const legendItems = [
  { label: '用户', type: 'user', color: '#ec4899' },
  { label: '特征类型', type: 'feature_type', color: '#6366f1' },
  { label: '特征值', type: 'feature_value', color: '#22c55e' },
  { label: '推理特征', type: 'inferred', color: '#f59e0b' }
]

const featureValues = computed(() => {
  if (!graphData.value?.nodes) return []
  const values = []
  graphData.value.nodes.forEach(node => {
    if (node.type === 'feature_value') {
      const typeNode = graphData.value.nodes.find(n => {
        const edge = graphData.value.edges.find(e => 
          e.target === node.id && e.source === n.id && e.relation === 'is_a'
        )
        return edge !== undefined
      })
      values.push({
        value: node.label,
        type: typeNode?.label || '未知'
      })
    }
  })
  return values
})

onMounted(async () => {
  await loadGraph()
})

async function loadGraph() {
  loading.value = true
  try {
    graphData.value = await store.loadKnowledgeGraph()
    await nextTick()
    renderGraph()
  } catch (e) {
    console.error('Failed to load graph:', e)
  } finally {
    loading.value = false
  }
}

function renderGraph() {
  if (!networkContainer.value || !graphData.value) return

  if (network) {
    network.destroy()
  }

  const nodes = graphData.value.nodes.map(node => {
    const bgColor = getNodeColor(node.type)
    const textColor = getContrastTextColor(bgColor)
    return {
      id: node.id,
      label: node.label,
      group: node.type,
      color: { background: bgColor, border: bgColor },
      font: { color: textColor, size: 16, bold: true },
      borderWidth: 3,
      shadow: true,
      shape: 'dot'
    }
  })

  const edges = graphData.value.edges.map(edge => ({
    from: edge.source,
    to: edge.target,
    label: edge.relation,
    arrows: 'to',
    color: { color: edge.inferred ? '#f59e0b' : '#6366f1' },
    dashes: edge.inferred,
    font: { color: '#a0a1ad', size: 11 }
  }))

  const data = { nodes, edges }

  const options = {
    nodes: {
      shape: 'dot',
      size: 25,
      font: {
        size: 12,
        face: 'Inter, sans-serif'
      },
      borderWidth: 3,
      shadow: true
    },
    edges: {
      width: 3,
      shadow: true,
      font: {
        size: 10,
        align: 'middle',
        color: '#a0a1ad'
      }
    },
    physics: {
      stabilization: true,
      barnesHut: {
        gravitationalConstant: -3000,
        springConstant: 0.05
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 200,
      zoomView: true,
      navigationButtons: false
    }
  }

  network = new Network(networkContainer.value, data, options)
}

function getNodeColor(type) {
  const colors = {
    'user': '#ec4899',
    'feature_type': '#6366f1',
    'feature_value': '#22c55e',
    'inferred': '#f59e0b'
  }
  return colors[type] || '#6b6c7d'
}

function getContrastTextColor(backgroundColor) {
  const hex = backgroundColor.replace('#', '')
  const r = parseInt(hex.substr(0, 2), 16)
  const g = parseInt(hex.substr(2, 2), 16)
  const b = parseInt(hex.substr(4, 2), 16)
  const brightness = (r * 299 + g * 587 + b * 114) / 1000
  return brightness > 128 ? '#000000' : '#ffffff'
}
</script>

<style scoped>
.knowledge-graph-view {
  display: flex;
  gap: 20px;
  height: calc(100vh - 112px);
}

.graph-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.graph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-primary);
}

.header-title {
  font-size: 16px;
  font-weight: 600;
}

.graph-container {
  flex: 1;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.network-container {
  width: 100%;
  height: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
  gap: 16px;
}

.empty-icon {
  color: var(--text-tertiary);
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.empty-desc {
  color: var(--text-secondary);
}

.graph-sidebar {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.stats-card,
.types-card,
.relations-card,
.features-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.types-list,
.relations-list,
.features-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.type-item,
.relation-item,
.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.type-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.type-name {
  font-size: 13px;
  color: var(--text-primary);
}

.relation-line {
  width: 30px;
  height: 3px;
  border-radius: 2px;
  background: #6366f1;
  flex-shrink: 0;
}

.relation-line.dashed {
  background: transparent;
  border: 2px dashed #6366f1;
}

.relation-name {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 500;
}

.relation-desc {
  font-size: 11px;
  color: var(--text-secondary);
  margin-left: auto;
}

.feature-type {
  font-size: 11px;
  color: var(--text-tertiary);
  background: var(--bg-primary);
  padding: 2px 8px;
  border-radius: 4px;
}

.feature-value {
  font-size: 13px;
  color: var(--text-primary);
  flex: 1;
}
</style>
