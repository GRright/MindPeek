<template>
  <div class="chat-view">
    <div class="chat-container">
      <div class="chat-header">
        <div class="user-selector">
          <el-icon :size="18"><User /></el-icon>
          <el-input
            v-model="userId"
            placeholder="输入用户ID"
            size="small"
            @change="changeUser"
            class="user-input"
          />
        </div>
      </div>

      <div class="chat-messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-chat">
          <div class="empty-icon">
            <el-icon :size="48"><ChatDotRound /></el-icon>
          </div>
          <p class="empty-title">开始对话</p>
          <p class="empty-desc">发送消息开始分析用户特征</p>
        </div>

        <transition-group name="message" tag="div" class="messages-wrapper">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['message', msg.role]"
        >
          <div class="message-avatar">
            <div class="avatar-circle" :class="msg.role">
              <el-icon v-if="msg.role === 'user'" :size="18"><User /></el-icon>
              <el-icon v-else :size="18"><Cpu /></el-icon>
            </div>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <div v-if="msg.content" class="message-text">{{ msg.content }}</div>
            </div>
            <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
          </div>
        </div>

        <div v-if="loading" class="message assistant">
          <div class="message-avatar">
            <div class="avatar-circle assistant">
              <el-icon :size="18"><Cpu /></el-icon>
            </div>
          </div>
          <div class="message-content">
            <div class="message-bubble loading">
              <div class="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
        </transition-group>
      </div>

      <div class="chat-input-area">
        <div class="input-wrapper">
          <el-tooltip content="深度思考" placement="top">
            <el-button
              class="think-btn"
              :class="{ active: deepThink }"
              @click="deepThink = !deepThink"
              :disabled="loading"
            >
              <el-icon :size="18"><MagicStick /></el-icon>
            </el-button>
          </el-tooltip>
          <el-input
            v-model="inputMessage"
            type="textarea"
            placeholder="输入消息... (Shift+Enter换行，Enter发送)"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 6 }"
            @keydown.enter.exact.prevent="sendMessage"
            :disabled="loading"
            class="message-input"
          />
          <el-button
            type="primary"
            @click="sendMessage"
            :disabled="loading || !inputMessage.trim()"
            class="send-btn"
          >
            <el-icon v-if="!loading" :size="20"><Promotion /></el-icon>
            <el-icon v-else class="is-loading" :size="20"><Loading /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <aside class="features-panel" v-if="extractedFeatures.length > 0">
      <div class="panel-header">
        <el-icon :size="18"><Document /></el-icon>
        <span>提取的特征</span>
      </div>
      <div class="features-list">
        <div
          v-for="(feature, index) in extractedFeatures"
          :key="index"
          class="feature-item"
        >
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
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useProfileStore } from '@/stores/profile'
import {
  User,
  Cpu,
  ChatDotRound,
  Promotion,
  Loading,
  Document,
  MagicStick
} from '@element-plus/icons-vue'

const store = useProfileStore()

const userId = ref(store.currentUserId)
const inputMessage = ref('')
const messages = ref([])
const extractedFeatures = ref([])
const loading = ref(false)
const messagesContainer = ref(null)
const deepThink = ref(false)

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
  if (!inputMessage.value.trim() || loading.value) return

  const message = inputMessage.value
  inputMessage.value = ''

  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: message,
    deepThink: deepThink.value,
    timestamp: new Date().toISOString()
  })

  scrollToBottom()

  loading.value = true
  try {
    const result = await store.sendMessage(message, deepThink.value)

    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: result.response || '消息已处理',
      timestamp: new Date().toISOString()
    })

    if (result.think_content) {
      try {
        const thinkData = JSON.parse(result.think_content)
        ElMessage.success(`深度分析完成`)
      } catch {
      }
    }

    extractedFeatures.value = result.features_extracted || []

    if (result.features_extracted && result.features_extracted.length > 0) {
      ElMessage.success(`提取了 ${result.features_extracted.length} 个特征`)
    }
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
  display: flex;
  gap: 20px;
  height: calc(100vh - 112px);
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
}

.user-selector {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-secondary);
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

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.empty-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.empty-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.avatar-circle.user {
  background: var(--accent-color);
  color: white;
}

.avatar-circle.assistant {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message.user .message-content {
  align-items: flex-end;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  line-height: 1.5;
  word-break: break-word;
}

.message.user .message-bubble {
  background: var(--accent-color);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.message-text {
  white-space: pre-wrap;
}

.message.assistant .message-bubble {
  border-bottom-left-radius: 4px;
}

.message-bubble.loading {
  padding: 16px 20px;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: bounce 1.4s infinite ease-in-out;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.message-time {
  font-size: 12px;
  color: var(--text-muted);
  padding: 0 4px;
}

.chat-input-area {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.think-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--bg-tertiary) !important;
  border: 1px solid var(--border-color) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary) !important;
  transition: all 0.2s ease;
}

.think-btn:hover:not(:disabled) {
  background: var(--bg-hover) !important;
  color: var(--text-primary) !important;
}

.think-btn.active {
  background: var(--accent-color) !important;
  border-color: var(--accent-color) !important;
  color: white !important;
}

.message-input {
  flex: 1;
}

.message-input :deep(.el-textarea__inner) {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  box-shadow: none;
  padding: 12px 16px;
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 15px;
  resize: none;
}

.message-input :deep(.el-textarea__inner::placeholder) {
  color: var(--text-muted);
}

.send-btn {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--accent-color) !important;
  border: none !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-hover) !important;
}

.send-btn:disabled {
  opacity: 0.5;
}

.features-panel {
  width: 320px;
  background: var(--bg-secondary);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-primary);
  font-weight: 500;
}

.features-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
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

.message-enter-active {
  transition: all 0.3s ease-out;
}

.message-leave-active {
  transition: all 0.2s ease-in;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.message-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.message-move {
  transition: transform 0.3s ease;
}
</style>