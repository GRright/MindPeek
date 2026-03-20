<template>
  <div class="knowledge-graph-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识图谱可视化</span>
          <div>
            <el-input
              v-model="userId"
              placeholder="用户ID（可选）"
              size="small"
              style="width: 150px; margin-right: 10px"
            />
            <el-button type="primary" @click="loadGraph" :loading="loading">
              加载图谱
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="graph-container" ref="graphContainer">
        <div v-if="!graphData" class="empty-state">
          <el-empty description="点击加载图谱查看知识网络" />
        </div>
        <div v-else ref="networkContainer" class="network-container"></div>
      </div>
    </el-card>
    
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>节点统计</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="总节点数">
              {{ graphData?.nodes?.length || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="总边数">
              {{ graphData?.edges?.length || 0 }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>节点类型分布</span>
          </template>
          <div class="type-list">
            <el-tag
              v-for="(count, type) in nodeTypeStats"
              :key="type"
              :type="getTypeColor(type)"
              style="margin: 5px"
            >
              {{ type }}: {{ count }}
            </el-tag>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { Network } from 'vis-network/standalone'

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
    color: getNodeColor(node.type),
    font: { size: 14 }
  }))
  
  const edges = graphData.value.edges.map(edge => ({
    from: edge.source,
    to: edge.target,
    label: edge.relation,
    arrows: 'to',
    color: { color: edge.inferred ? '#ff9800' : '#2196f3' },
    dashes: edge.inferred
  }))
  
  const data = { nodes, edges }
  
  const options = {
    nodes: {
      shape: 'dot',
      size: 16,
      font: {
        size: 12,
        face: 'Tahoma'
      },
      borderWidth: 2,
      shadow: true
    },
    edges: {
      width: 2,
      shadow: true,
      font: {
        size: 10,
        align: 'middle'
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
    'user': '#e91e63',
    'MBTI': '#9c27b0',
    '大五人格': '#2196f3',
    '行为习惯': '#ff9800',
    '潜在想法': '#f44336',
    'feature': '#4caf50'
  }
  return colors[type] || '#607d8b'
}

function getTypeColor(type) {
  const colors = {
    'user': 'danger',
    'MBTI': '',
    '大五人格': 'primary',
    '行为习惯': 'warning',
    '潜在想法': 'danger',
    'feature': 'success'
  }
  return colors[type] || 'info'
}
</script>

<style scoped>
.knowledge-graph-view {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.graph-container {
  height: 500px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.network-container {
  width: 100%;
  height: 100%;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.type-list {
  display: flex;
  flex-wrap: wrap;
}
</style>
