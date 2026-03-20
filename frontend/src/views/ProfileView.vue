<template>
  <div class="profile-view">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="user-card">
          <template #header>
            <div class="card-header">
              <span>用户信息</span>
              <el-input
                v-model="userId"
                placeholder="用户ID"
                size="small"
                style="width: 120px"
                @change="loadProfile"
              />
            </div>
          </template>

          <div v-if="profileSummary" class="user-info">
            <div class="avatar-section">
              <div class="avatar-circle">
                <el-avatar :size="70" :style="{ background: avatarColor }">
                  {{ userId.charAt(0).toUpperCase() }}
                </el-avatar>
              </div>
              <h3>{{ userId }}</h3>
              <el-tag :type="confidenceLevel" size="small">
                置信度: {{ (profileSummary.confidence_score * 100).toFixed(0) }}%
              </el-tag>
            </div>

            <el-divider />

            <div class="stats-section">
              <el-row>
                <el-col :span="12">
                  <div class="stat-item">
                    <div class="stat-value">{{ profileSummary.total_features }}</div>
                    <div class="stat-label">特征数</div>
                  </div>
                </el-col>
                <el-col :span="12">
                  <div class="stat-item">
                    <div class="stat-value">{{ profileSummary.conversation_count }}</div>
                    <div class="stat-label">对话轮数</div>
                  </div>
                </el-col>
              </el-row>
            </div>

            <el-divider />

            <div v-if="profileSummary.mbti" class="mbti-section">
              <h4>性格类型</h4>
              <div class="mbti-display">
                <span
                  v-for="(char, idx) in profileSummary.mbti.split('')"
                  :key="idx"
                  class="mbti-char"
                  :class="{ active: mbtiActive[idx] }"
                  @mouseenter="highlightMbti(idx)"
                  @mouseleave="resetMbti"
                >
                  {{ char }}
                </span>
              </div>
              <div class="mbti-meaning">{{ getMbtiMeaning() }}</div>
            </div>
          </div>
          <el-empty v-else description="暂无用户数据" />
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>用户画像可视化</span>
              <el-button text @click="refreshProfile" :icon="Refresh">刷新</el-button>
            </div>
          </template>

          <el-tabs v-model="activeTab" class="profile-tabs">
            <el-tab-pane label="人格雷达图" name="radar">
              <div ref="radarContainer" class="chart-container"></div>
            </el-tab-pane>

            <el-tab-pane label="特征关系图" name="graph">
              <div ref="graphContainer" class="chart-container"></div>
            </el-tab-pane>

            <el-tab-pane label="特征分布" name="pie">
              <div ref="pieContainer" class="chart-container"></div>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <el-card class="features-card" style="margin-top: 20px">
          <template #header>
            <span>详细特征</span>
          </template>
          <div class="features-timeline">
            <el-timeline>
              <el-timeline-item
                v-for="(feature, index) in allFeatures"
                :key="index"
                :type="getFeatureColor(feature.feature_type)"
                :hollow="feature.confidence < 0.7"
              >
                <div class="feature-item">
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
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import { useProfileStore } from '@/stores/profile'
import * as echarts from 'echarts'

const store = useProfileStore()

const userId = ref(store.currentUserId)
const activeTab = ref('radar')
const profileSummary = ref(null)
const allFeatures = ref([])

const radarContainer = ref(null)
const graphContainer = ref(null)
const pieContainer = ref(null)

let radarChart = null
let graphChart = null
let pieChart = null

const mbtiActive = ref([false, false, false, false])

const confidenceLevel = computed(() => {
  if (!profileSummary.value) return 'info'
  const score = profileSummary.value.confidence_score
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'danger'
})

const avatarColor = computed(() => {
  const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
  let hash = 0
  for (let i = 0; i < userId.value.length; i++) {
    hash = userId.value.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
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

  if (!radarChart) {
    radarChart = echarts.init(radarContainer.value)
  }

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
    tooltip: {
      trigger: 'item'
    },
    radar: {
      indicator: indicators,
      radius: '65%',
      axisName: {
        color: '#333',
        fontSize: 12
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '大五人格',
        areaStyle: {
          color: 'rgba(102, 126, 234, 0.3)'
        },
        lineStyle: {
          color: '#667eea'
        },
        itemStyle: {
          color: '#667eea'
        }
      }],
      emphasis: {
        lineStyle: {
          width: 3
        }
      }
    }]
  }

  radarChart.setOption(option)
}

function renderGraphChart() {
  if (!graphContainer.value) return

  if (!graphChart) {
    graphChart = echarts.init(graphContainer.value)
  }

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
      width: f.confidence * 5,
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [
          { offset: 0, color: '#667eea' },
          { offset: 1, color: getFeatureColor(f.feature_type) }
        ]
      }
    }
  }))

  const option = {
    tooltip: {
      formatter: '{b}'
    },
    legend: [{
      data: categories,
      textStyle: { fontSize: 10 }
    }],
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      label: {
        show: true,
        position: 'right',
        fontSize: 10
      },
      categories: categories.map((name, idx) => ({ name, itemStyle: { color: getCategoryColor(idx) } })),
      nodes: nodes,
      links: links,
      lineStyle: {
        curveness: 0.3
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

  if (!pieChart) {
    pieChart = echarts.init(pieContainer.value)
  }

  const typeCount = {}
  allFeatures.value.forEach(f => {
    typeCount[f.feature_type] = (typeCount[f.feature_type] || 0) + 1
  })

  const pieData = Object.entries(typeCount).map(([name, value]) => ({
    name,
    value
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: { fontSize: 11 }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
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
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: pieData,
      color: ['#667eea', '#f44336', '#ff9800', '#4caf50', '#2196f3', '#9c27b0']
    }]
  }

  pieChart.setOption(option)
}

function getCategoryColor(idx) {
  const colors = ['#9c27b0', '#2196f3', '#ff9800', '#f44336', '#4caf50', '#e91e63']
  return colors[idx] || '#607d8b'
}

function getFeatureColor(type) {
  const colors = {
    'MBTI': '#9c27b0',
    '大五人格': '#2196f3',
    '行为习惯': '#ff9800',
    '潜在想法': '#f44336',
    '兴趣爱好': '#4caf50'
  }
  return colors[type] || '#607d8b'
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

function getMbtiMeaning() {
  if (!profileSummary.value?.mbti) return ''
  const meanings = {
    'I': '内向型 - 从内心世界获取能量',
    'E': '外向型 - 从外部世界获取能量',
    'N': '直觉型 - 关注抽象概念',
    'S': '感觉型 - 关注具体细节',
    'T': '思考型 - 依据逻辑决策',
    'F': '情感型 - 依据价值观决策',
    'J': '判断型 - 喜欢计划和控制',
    'P': '感知型 - 喜欢灵活应变'
  }
  return profileSummary.value.mbti.split('').map(c => meanings[c]).join(' / ')
}
</script>

<style scoped>
.profile-view {
  height: 100%;
  overflow-y: auto;
}

.user-card {
  height: auto;
  min-height: calc(100vh - 160px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.avatar-section {
  text-align: center;
  padding: 10px 0;
}

.avatar-circle {
  margin-bottom: 10px;
}

.avatar-section h3 {
  margin: 10px 0;
  color: #303133;
}

.stats-section {
  padding: 5px 0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.mbti-section {
  text-align: center;
}

.mbti-section h4 {
  margin-bottom: 10px;
  color: #606266;
}

.mbti-display {
  display: flex;
  justify-content: center;
  gap: 5px;
  margin-bottom: 10px;
}

.mbti-char {
  width: 36px;
  height: 36px;
  line-height: 36px;
  border-radius: 50%;
  background: #f0f2f5;
  color: #909399;
  font-weight: bold;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.mbti-char.active {
  background: #667eea;
  color: white;
  transform: scale(1.2);
}

.mbti-meaning {
  font-size: 11px;
  color: #909399;
  line-height: 1.4;
}

.chart-card {
  min-height: 450px;
}

.chart-container {
  width: 100%;
  height: 350px;
}

.features-card {
  max-height: 400px;
  overflow-y: auto;
}

.features-timeline {
  padding: 10px 0;
}

.feature-item {
  padding: 5px 0;
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.confidence {
  font-size: 12px;
  color: #909399;
}

.feature-value {
  font-weight: 500;
  color: #303133;
  margin-bottom: 3px;
}

.feature-reasoning {
  font-size: 12px;
  color: #909399;
}
</style>
