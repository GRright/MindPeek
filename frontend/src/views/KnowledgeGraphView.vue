<template>
  <div class="knowledge-graph-view">
    <div class="graph-main">
      <div class="graph-header">
        <div class="header-left">
          <el-icon :size="20"><Connection /></el-icon>
          <span class="header-title">知识图谱</span>
        </div>
        <div class="header-actions">
          <el-input
            v-model="userId"
            placeholder="用户ID（可选）"
            size="default"
            class="user-input"
          />
          <el-button type="primary" @click="loadGraph" :loading="loading" class="load-btn">
            加载图谱
          </el-button>
        </div>
      </div>

      <div class="graph-container" ref="graphContainer">
        <div v-if="!graphData" class="empty-state">
          <div class="empty-icon">
            <el-icon :size="64"><Share /></el-icon>
          </div>
          <p class="empty-title">知识图谱</p>
          <p class="empty-desc">点击加载图谱查看用户特征关系网络</p>
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
        <div class="card-title">节点类型分布</div>
        <div class="types-list">
          <div
            v-for="(count, type) in nodeTypeStats"
            :key="type"
            class="type-item"
          >
            <div class="type-dot" :style="{ background: getNodeColor(type) }"></div>
            <span class="type-name">{{ type }}</span>
            <span class="type-count">{{ count }}</span>
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

const userId = ref('')
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

onMounted(async () => {
  userId.value = store.currentUserId
})

async function loadGraph() {
  loading.value = true
  try {
    if (userId.value) {
      graphData.value = await store.loadKnowledgeGraph()
    } else {
      const api = (await import('@/api')).default
      graphData.value = await api.getKnowledgeGraph()
    }

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

  const nodes = graphData.value.nodes.map(node => ({
    id: node.id,
    label: node.label,
    group: node.type,
    color: { background: getNodeColor(node.type), border: getNodeColor(node.type) },
    font: { color: '#f0f0f2', size: 14 },
    borderWidth: 2,
    shadow: true
  }))

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
      size: 20,
      font: {
        size: 12,
        face: 'Inter, sans-serif'
      },
      borderWidth: 2,
      shadow: true
    },
    edges: {
      width: 2,
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
        gravitationalConstant: -2000,
        springConstant: 0.04
      }
    },
    interaction: {
      hover: true,
      tooltipDelay: 200,
      zoomView: true
    }
  }

  network = new Network(networkContainer.value, data, options)
}

function getNodeColor(type) {
  const colors = {
    'user': '#ec4899',
    'MBTI': '#8b5cf6',
    '大五人格': '#2196f3',
    '行为习惯': '#f59e0b',
    '潜在想法': '#ef4444',
    'feature': '#22c55e'
  }
  return colors[type] || '#6b6c7d'
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-input {
  width: 200px;
}

.user-input :deep(.el-input__wrapper) {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  box-shadow: none;
}

.user-input :deep(.el-input__inner) {
  color: var(--text-primary);
}

.load-btn {
  background: var(--accent-color) !important;
  border: none !important;
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
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.empty-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
}

.graph-sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-card,
.types-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: 10px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.types-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.type-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.type-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.type-name {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
}

.type-count {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
</style>