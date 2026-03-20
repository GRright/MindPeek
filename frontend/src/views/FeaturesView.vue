<template>
  <div class="features-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>特征管理</span>
          <div>
            <el-input
              v-model="userId"
              placeholder="用户ID"
              size="small"
              style="width: 150px; margin-right: 10px"
              @change="loadFeatures"
            />
            <el-button type="primary" @click="showAddDialog = true">
              添加特征
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="features" style="width: 100%" v-loading="loading">
        <el-table-column prop="feature_type" label="特征类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getFeatureTagType(row.feature_type)">
              {{ row.feature_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="feature_value" label="特征值" min-width="200" />
        <el-table-column prop="confidence" label="置信度" width="150">
          <template #default="{ row }">
            <el-progress
              :percentage="row.confidence * 100"
              :stroke-width="8"
              :color="getConfidenceColor(row.confidence)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="source_message" label="来源消息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reasoning" label="推理依据" min-width="200" show-overflow-tooltip />
        <el-table-column prop="updated_at" label="更新时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" text @click="deleteFeature(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadFeatures"
        />
      </div>
    </el-card>
    
    <el-dialog v-model="showAddDialog" title="添加特征" width="500px">
      <el-form :model="newFeature" label-width="100px">
        <el-form-item label="特征类型">
          <el-select v-model="newFeature.feature_type" placeholder="选择类型" style="width: 100%">
            <el-option label="MBTI" value="MBTI" />
            <el-option label="大五人格" value="大五人格" />
            <el-option label="行为习惯" value="行为习惯" />
            <el-option label="潜在想法" value="潜在想法" />
            <el-option label="兴趣爱好" value="兴趣爱好" />
            <el-option label="价值观" value="价值观" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="特征值">
          <el-input v-model="newFeature.feature_value" placeholder="输入特征值" />
        </el-form-item>
        
        <el-form-item label="置信度">
          <el-slider v-model="newFeature.confidence" :min="0" :max="1" :step="0.1" show-input />
        </el-form-item>
        
        <el-form-item label="来源消息">
          <el-input
            v-model="newFeature.source_message"
            type="textarea"
            :rows="2"
            placeholder="可选"
          />
        </el-form-item>
        
        <el-form-item label="推理依据">
          <el-input
            v-model="newFeature.reasoning"
            type="textarea"
            :rows="2"
            placeholder="可选"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addFeature" :loading="adding">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProfileStore } from '@/stores/profile'

const store = useProfileStore()

const userId = ref(store.currentUserId)
const features = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showAddDialog = ref(false)
const adding = ref(false)
const newFeature = ref({
  feature_type: '',
  feature_value: '',
  confidence: 0.7,
  source_message: '',
  reasoning: ''
})

onMounted(async () => {
  await loadFeatures()
})

async function loadFeatures() {
  loading.value = true
  try {
    const data = await store.loadProfile()
    features.value = data.features || []
    total.value = features.value.length
  } catch (e) {
    console.error('Failed to load features:', e)
  } finally {
    loading.value = false
  }
}

async function addFeature() {
  if (!newFeature.value.feature_type || !newFeature.value.feature_value) {
    ElMessage.warning('请填写特征类型和特征值')
    return
  }
  
  adding.value = true
  try {
    await store.addFeature(newFeature.value)
    ElMessage.success('特征添加成功')
    showAddDialog.value = false
    newFeature.value = {
      feature_type: '',
      feature_value: '',
      confidence: 0.7,
      source_message: '',
      reasoning: ''
    }
    await loadFeatures()
  } catch (e) {
    ElMessage.error('添加失败: ' + e.message)
  } finally {
    adding.value = false
  }
}

function deleteFeature(row) {
  ElMessageBox.confirm('确定要删除该特征吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.info('删除功能待实现')
  }).catch(() => {})
}

function getFeatureTagType(type) {
  const types = {
    'MBTI': 'primary',
    '大五人格': 'success',
    '行为习惯': 'warning',
    '潜在想法': 'danger',
    '兴趣爱好': 'info'
  }
  return types[type] || ''
}

function getConfidenceColor(confidence) {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.6) return '#e6a23c'
  return '#f56c6c'
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.features-view {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>
