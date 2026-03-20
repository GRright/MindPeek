<template>
  <div class="chat-view">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card class="chat-card">
          <template #header>
            <div class="card-header">
              <span>对话分析</span>
              <el-input
                v-model="userId"
                placeholder="用户ID"
                style="width: 200px"
                size="small"
                @change="changeUser"
              />
            </div>
          </template>
          
          <div class="chat-messages" ref="messagesContainer">
            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="['message', msg.role]"
            >
              <div class="message-avatar">
                <el-avatar :size="36" :icon="msg.role === 'user' ? 'User' : 'Monitor'" />
              </div>
              <div class="message-content">
                <div class="message-text">{{ msg.content }}</div>
                <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
            </div>
          </div>
          
          <div class="chat-input">
            <el-input
              v-model="inputMessage"
              placeholder="输入消息进行对话分析..."
              @keyup.enter="sendMessage"
              :disabled="loading"
            >
              <template #append>
                <el-button @click="sendMessage" :loading="loading">
                  发送
                </el-button>
              </template>
            </el-input>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card class="features-card">
          <template #header>
            <span>实时提取的特征</span>
          </template>
          
          <div v-if="extractedFeatures.length === 0" class="empty-state">
            <el-empty description="发送消息后将自动提取特征" :image-size="100" />
          </div>
          
          <div v-else class="features-list">
            <div
              v-for="(feature, index) in extractedFeatures"
              :key="index"
              class="feature-item"
            >
              <div class="feature-header">
                <el-tag :type="getFeatureTagType(feature.feature_type)">
                  {{ feature.feature_type }}
                </el-tag>
                <el-progress
                  :percentage="feature.confidence * 100"
                  :stroke-width="6"
                  style="width: 100px"
                />
              </div>
              <div class="feature-value">{{ feature.feature_value }}</div>
              <div v-if="feature.reasoning" class="feature-reasoning">
                {{ feature.reasoning }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useProfileStore } from '@/stores/profile'

const store = useProfileStore()

const userId = ref(store.currentUserId)
const inputMessage = ref('')
const messages = ref([])
const extractedFeatures = ref([])
const loading = ref(false)
const messagesContainer = ref(null)

onMounted(async () => {
  await loadConversations()
})

async function loadConversations() {
  try {
    const data = await store.loadConversations()
    messages.value = data || []
    scrollToBottom()
  } catch (e) {
    console.error('Failed to load conversations:', e)
  }
}

async function sendMessage() {
  if (!inputMessage.value.trim()) return
  
  const message = inputMessage.value
  inputMessage.value = ''
  
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  })
  
  scrollToBottom()
  
  loading.value = true
  try {
    const result = await store.sendMessage(message)
    
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '消息已处理，特征已更新',
      timestamp: new Date().toISOString()
    })
    
    extractedFeatures.value = result.features_extracted || []
    
    ElMessage.success(`提取了 ${extractedFeatures.value.length} 个特征`)
    scrollToBottom()
  } catch (e) {
    ElMessage.error('发送失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

function changeUser() {
  store.setUserId(userId.value)
  messages.value = []
  extractedFeatures.value = []
  loadConversations()
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
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
</script>

<style scoped>
.chat-view {
  height: 100%;
}

.chat-card {
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}

.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
}

.message {
  display: flex;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  margin: 0 10px;
}

.message-content {
  max-width: 70%;
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  display: inline-block;
  padding: 10px 15px;
  border-radius: 8px;
  background: white;
  text-align: left;
}

.message.user .message-text {
  background: #409eff;
  color: white;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.chat-input {
  padding: 15px;
  border-top: 1px solid #ebeef5;
}

.features-card {
  height: calc(100vh - 140px);
  overflow-y: auto;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.feature-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.feature-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.feature-value {
  font-weight: 500;
  margin-bottom: 5px;
}

.feature-reasoning {
  font-size: 12px;
  color: #909399;
}

.empty-state {
  padding: 40px 0;
}
</style>
