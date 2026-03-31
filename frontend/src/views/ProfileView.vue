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
              <span 
                class="overview-value" 
                :title="getFeatureValueByType('职业') || '未知'"
              >
                {{ getFeatureValueByType('职业') || '未知' }}
              </span>
            </div>
            <div class="overview-item">
              <span class="overview-label">性格</span>
              <span 
                class="overview-value" 
                :title="getMbtiSummary()"
              >
                {{ getMbtiSummary() }}
              </span>
            </div>
            <div class="overview-item">
              <span class="overview-label">兴趣</span>
              <span 
                class="overview-value" 
                :title="getTopInterests()"
              >
                {{ getTopInterests() }}
              </span>
            </div>
            <div class="overview-item">
              <span class="overview-label">生活方式</span>
              <span 
                class="overview-value" 
                :title="getLifestyleSummary()"
              >
                {{ getLifestyleSummary() }}
              </span>
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
            <el-tab-pane label="特征总览" name="overview">
              <div ref="overviewContainer" class="chart-container"></div>
            </el-tab-pane>
            <el-tab-pane label="分布图" name="pie">
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
            <div
              v-for="(prediction, index) in predictions"
              :key="prediction.id || index"
              class="prediction-item"
              :class="'rank-' + (index + 1)"
            >
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
              <p class="empty-hint">点击"生成预测"按钮，AI 将基于您的特征进行智能预测</p>
            </div>

            <div v-if="generatingPredictions" class="loading-predictions">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>AI 正在分析预测中...</span>
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
import { Refresh, Document, Loading, Search, Promotion, MagicStick } from '@element-plus/icons-vue'
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

const mbtiActive = ref([false, false, false, false])

const confidencePercent = computed(() => {
  // 使用所有特征的平均置信度作为总体置信度
  if (!allFeatures.value || allFeatures.value.length === 0) return 0
  const sum = allFeatures.value.reduce((acc, f) => acc + (f.confidence || 0), 0)
  const avg = sum / allFeatures.value.length
  return (avg * 100).toFixed(0)
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
    
    // 总是尝试获取最新预测（优先使用缓存，没有缓存时自动生成）
    await generatePredictions(true)
  } catch (e) {
    console.error('Failed to load profile:', e)
  }
}

async function generatePredictions(silent = true) {
  // 静默模式：不显示 loading 和提示
  if (silent) {
    generatingPredictions.value = false
  } else {
    generatingPredictions.value = true
  }
  
  try {
    const response = await fetch(`/api/profile/${userId.value}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        force_refresh: false  // 总是优先使用缓存
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      predictions.value = result.predictions || []
      
      // 只在非静默模式下显示提示
      if (!silent) {
        if (result.cached) {
          ElMessage.success('已加载缓存的预测结果')
        } else {
          ElMessage.success('AI 预测已生成')
        }
      }
    } else if (!silent) {
      ElMessage.error('生成预测失败')
    }
  } catch (e) {
    console.error('生成预测失败:', e)
    if (!silent) {
      ElMessage.error('生成预测失败：' + e.message)
    }
  } finally {
    generatingPredictions.value = false
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

function renderOverviewChart() {
  if (!overviewContainer.value) return

  if (overviewChart) {
    overviewChart.dispose()
  }
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

  // 统计每个特征类型的数量和平均置信度
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

  // 计算平均置信度
  Object.keys(typeStats).forEach(type => {
    typeStats[type].avgConfidence = typeStats[type].totalConfidence / typeStats[type].count
  })

  // 构建中心节点（用户）和类别节点
  const nodes = [
    {
      id: 'user',
      name: userId.value,
      category: 0,
      symbolSize: 80,
      itemStyle: {
        color: '#6366f1',
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
    }
  ]

  // 为每个特征类型添加节点
  const categories = Object.keys(typeStats)
  categories.forEach((type, idx) => {
    const stats = typeStats[type]
    const size = 40 + (stats.count * 3) // 根据特征数量调整节点大小
    
    nodes.push({
      id: `type_${type}`,
      name: type,
      category: 1,
      symbolSize: Math.min(size, 70),
      itemStyle: {
        color: stats.colors,
        shadowColor: `rgba(${hexToRgb(stats.colors)}, 0.4)`,
        shadowBlur: 15
      },
      label: {
        show: true,
        position: 'bottom',
        fontSize: 13,
        fontWeight: 600,
        color: '#374151',
        formatter: (params) => {
          return `{name|${params.name}}\n{count|${stats.count}个特征}\n{conf|${(stats.avgConfidence * 100).toFixed(0)}%}`
        },
        rich: {
          name: {
            fontSize: 13,
            fontWeight: 600,
            lineHeight: 20
          },
          count: {
            fontSize: 11,
            color: '#6b7280',
            lineHeight: 16
          },
          conf: {
            fontSize: 11,
            color: '#22c55e',
            fontWeight: 600,
            lineHeight: 16
          }
        }
      }
    })
  })

  // 创建用户到各个类别的连接
  const links = categories.map(type => ({
    source: 'user',
    target: `type_${type}`,
    value: typeStats[type].avgConfidence,
    lineStyle: {
      width: 3 + (typeStats[type].avgConfidence * 3),
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 1, y2: 0,
        colorStops: [
          { offset: 0, color: '#6366f1' },
          { offset: 1, color: typeStats[type].colors }
        ]
      },
      curveness: 0.2,
      opacity: 0.8
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
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151'
      },
      formatter: (params) => {
        if (params.dataType === 'edge') {
          return `<div style="padding: 8px;">
            <div style="color: #6366f1; font-weight: 600; margin-bottom: 8px;">特征类别</div>
            <div>平均置信度：${((params.data.value || 0) * 100).toFixed(0)}%</div>
          </div>`
        }
        if (params.name === userId.value) {
          return `<div style="padding: 8px;">
            <div style="color: #6366f1; font-weight: 600; font-size: 14px; margin-bottom: 8px;">${params.name}</div>
            <div>特征类型：${categories.length} 种</div>
            <div>特征总数：${displayFeatures.length} 个</div>
          </div>`
        }
        const stats = typeStats[params.name]
        return `<div style="padding: 8px;">
          <div style="color: ${stats.colors}; font-weight: 600; font-size: 14px; margin-bottom: 8px;">${params.name}</div>
          <div>特征数量：<span style="color: #22c55e; font-weight: 600;">${stats.count} 个</span></div>
          <div>平均置信度：<span style="color: #22c55e; font-weight: 600;">${(stats.avgConfidence * 100).toFixed(0)}%</span></div>
        </div>`
      }
    },
    legend: {
      show: false
    },
    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      label: {
        show: true,
        position: 'bottom'
      },
      categories: [
        { name: '用户' },
        { name: '特征类型' }
      ],
      nodes: nodes,
      links: links,
      lineStyle: {
        curveness: 0.2
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 8
        }
      },
      force: {
        repulsion: 600,
        gravity: 0.1,
        edgeLength: 180
      }
    }]
  }

  overviewChart.setOption(option)
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result 
    ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
    : '99, 102, 241'
}

function renderPieChart() {
  if (!pieContainer.value) return

  if (pieChart) {
    pieChart.dispose()
  }
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

  // 计算平均置信度
  Object.keys(typeCount).forEach(type => {
    typeConfidence[type] = typeConfidence[type] / typeCount[type]
  })

  // 按特征数量排序
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
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: { color: '#374151' },
      formatter: (params) => {
        const data = sortedData[params[0].dataIndex]
        return `<div style="padding: 8px;">
          <div style="color: ${data.itemStyle.color}; font-weight: 600; font-size: 14px; margin-bottom: 8px;">${data.name}</div>
          <div>特征数量：<span style="color: #6366f1; font-weight: 600;">${data.value} 个</span></div>
          <div>平均置信度：<span style="color: #22c55e; font-weight: 600;">${(data.confidence * 100).toFixed(0)}%</span></div>
          <div>占比：<span style="color: #f59e0b; font-weight: 600;">${((data.value / allFeatures.value.length) * 100).toFixed(1)}%</span></div>
        </div>`
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
      axisLine: {
        lineStyle: {
          color: 'var(--border-color)'
        }
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      name: '特征数量',
      nameTextStyle: {
        color: 'var(--text-muted)',
        fontSize: 12
      },
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      splitLine: {
        lineStyle: {
          color: 'var(--border-color)',
          type: 'dashed',
          opacity: 0.3
        }
      },
      axisLabel: {
        color: 'var(--text-muted)',
        fontSize: 11
      }
    },
    series: [
      {
        type: 'bar',
        data: sortedData,
        barWidth: '50%',
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          shadowColor: 'rgba(0, 0, 0, 0.1)',
          shadowBlur: 10,
          shadowOffsetY: 5
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
            count: {
              fontSize: 12,
              fontWeight: 600,
              lineHeight: 16
            },
            percent: {
              fontSize: 10,
              color: 'var(--text-muted)',
              lineHeight: 14
            }
          }
        },
        emphasis: {
          itemStyle: {
            shadowColor: 'rgba(0, 0, 0, 0.2)',
            shadowBlur: 15,
            shadowOffsetY: 8
          },
          label: {
            fontSize: 13,
            fontWeight: 'bold'
          }
        }
      }
    ]
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
  height: calc(100vh - 7rem);
  min-height: 25rem;
  overflow-y: auto;
}

.profile-grid {
  display: grid;
  grid-template-columns: 20rem 1fr;
  gap: 1.25rem;
}

.profile-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.user-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 1rem;
  padding: 1.5rem;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.user-card:hover {
  transform: translateY(-0.25rem);
  box-shadow: 0 0.5rem 1.5rem rgba(99, 102, 241, 0.15);
}

.user-avatar {
  margin-bottom: 1rem;
}

.avatar-ring {
  width: 6.25rem;
  height: 6.25rem;
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
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text-primary);
}

.user-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.user-badge {
  margin-bottom: 1.25rem;
}

.mbti-badge {
  display: inline-block;
  padding: 0.375rem 1rem;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-radius: 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
}

.user-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem 0;
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1.25rem;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.stat-divider {
  width: 1px;
  height: 2.5rem;
  background: var(--border-color);
}

.user-input-section {
  padding-top: 0.5rem;
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
  border-radius: 1rem;
  padding: 1.25rem;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.overview-card:hover {
  transform: translateY(-0.25rem);
  box-shadow: 0 0.5rem 1.5rem rgba(99, 102, 241, 0.15);
}

.card-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.overview-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.overview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.625rem 0.75rem;
  background: var(--bg-tertiary);
  border-radius: 0.625rem;
}

.overview-label {
  font-size: 0.8125rem;
  color: var(--text-muted);
  font-weight: 500;
}

.overview-value {
  font-size: 0.8125rem;
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
  border-radius: 1rem;
  padding: 1.25rem;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.mbti-card:hover {
  transform: translateY(-0.25rem);
  box-shadow: 0 0.5rem 1.5rem rgba(99, 102, 241, 0.15);
}

.mbti-chars {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
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
  height: 40px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  flex: 1;
  height: 40px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.5;
  display: flex;
  align-items: center;
  height: 40px;
}

.predict-btn {
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
  border: none !important;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  vertical-align: middle;
  height: 32px;
  padding: 0 16px;
  margin-top: 0;
}

.predict-btn:hover {
  background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
}

.prediction-count {
  font-size: 13px;
  color: var(--text-muted);
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

.predictions-card {
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
  background: var(--bg-tertiary);
  border-radius: 3px;
}

.predictions-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.prediction-item {
  display: flex;
  gap: 14px;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
  animation: slideIn 0.4s ease both;
}

.prediction-item:hover {
  border-color: var(--accent-color);
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
}

.prediction-item.rank-1 {
  border-left: 4px solid #f59e0b;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.05), var(--bg-tertiary));
}

.prediction-item.rank-2 {
  border-left: 4px solid #9ca3af;
  background: linear-gradient(135deg, rgba(156, 163, 175, 0.05), var(--bg-tertiary));
}

.prediction-item.rank-3 {
  border-left: 4px solid #b45309;
  background: linear-gradient(135deg, rgba(180, 83, 9, 0.05), var(--bg-tertiary));
}

.prediction-rank {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
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
  color: var(--text-muted);
  line-height: 1.4;
  background: var(--bg-secondary);
  padding: 10px 12px;
  border-radius: 8px;
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
  font-size: 11px;
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

.empty-hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
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
  padding: 3.75rem 1.25rem;
  color: var(--text-muted);
}

.empty-features p {
  margin-top: 0.75rem;
  font-size: 0.875rem;
}

@media screen and (max-width: 64rem) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
  
  .profile-sidebar {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(15.625rem, 1fr));
    gap: 1rem;
  }
}

@media screen and (max-width: 48rem) {
  .profile-view {
    height: auto;
    min-height: calc(100vh - 7rem);
  }
  
  .profile-grid {
    gap: 0.75rem;
  }
}

@media screen and (min-width: 120rem) {
  .profile-view {
    max-width: 87.5rem;
    margin: 0 auto;
  }
}
</style>