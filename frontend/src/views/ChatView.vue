<template>
  <div class="chat-view">
    <div class="chat-container">
      <div class="chat-header">
        <div class="user-selector">
          <el-icon :size="18"><User /></el-icon>
          <el-input
            v-model="userId"
            placeholder="输入用户 ID"
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
              <div v-if="msg.think_content && !msg.is_streaming" class="think-content">
                <el-collapse v-model="msg.activeCollapse" accordion>
                  <el-collapse-item :name="msg.id">
                    <template #title>
                      <span style="font-weight: 600">💭 深度思考过程</span>
                    </template>
                    <div class="think-text">{{ formatThinkContent(msg.think_content) }}</div>
                  </el-collapse-item>
                </el-collapse>
              </div>
              <div v-if="msg.content" v-html="renderMarkdown(msg.content)" class="message-text markdown-content"></div>
              <div v-if="msg.is_streaming && !msg.content" class="loading-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
            <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
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
            placeholder="输入消息... (Shift+Enter 换行，Enter 发送)"
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
import MarkdownIt from 'markdown-it'
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
const md = new MarkdownIt()

const userId = ref(store.currentUserId)
const inputMessage = ref('')
const messages = ref([])
const extractedFeatures = ref([])
const loading = ref(false)
const messagesContainer = ref(null)
const deepThink = ref(false)

// 格式化深度思考内容，移除 think 标签
function formatThinkContent(content) {
  if (!content) return ''
  let result = content
  while (result.includes('<end_of_thought>')) {
    result = result.substring(0, result.indexOf('<end_of_thought>')) + result.substring(result.indexOf('<end_of_thought>') + '<end_of_thought>'.length)
  }
  while (result.includes('<start_of_thought>')) {
    result = result.substring(0, result.indexOf('<start_of_thought>')) + result.substring(result.indexOf('<start_of_thought>') + '<start_of_thought>'.length)
  }
  return result.trim()
}

onMounted(async () => {
  await loadLocalConversations()
})

async function loadLocalConversations() {
  try {
    const saved = localStorage.getItem(`chat_${userId.value}`)
    if (saved) {
      const data = JSON.parse(saved)
      messages.value = data.map((msg, idx) => ({
        ...msg,
        id: Date.now() + idx,
        is_streaming: false,
        activeCollapse: [],
        timestamp: new Date().toISOString()
      }))
    }
  } catch (e) {
    console.error('加载本地对话失败:', e)
  }
}

async function sendMessage() {
  if (!inputMessage.value.trim() || loading.value) return

  const message = inputMessage.value
  inputMessage.value = ''

  const userMsgId = Date.now()
  messages.value.push({
    id: userMsgId,
    role: 'user',
    content: message,
    deepThink: deepThink.value,
    timestamp: new Date().toISOString()
  })

  scrollToBottom()

  loading.value = true
  try {
    const assistantMsgId = Date.now() + 1
    messages.value.push({
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      think_content: null,
      activeCollapse: [],
      is_streaming: true,
      timestamp: new Date().toISOString()
    })

    const response = await fetch('http://localhost:8000/api/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId.value,
        message: message,
        extract_features: true,
        deep_think: deepThink.value
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullResponse = ''
    let thinkContent = null

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.substring(6))
            if (data.type === 'chunk') {
              fullResponse += data.content
              const msg = messages.value.find(m => m.id === assistantMsgId)
              if (msg) {
                msg.content = fullResponse
              }
              scrollToBottom()
            } else if (data.type === 'think' && data.content) {
              thinkContent = data.content
              const msg = messages.value.find(m => m.id === assistantMsgId)
              if (msg) {
                msg.think_content = thinkContent
              }
            } else if (data.type === 'done') {
              thinkContent = data.think_content
              const msg = messages.value.find(m => m.id === assistantMsgId)
              if (msg) {
                msg.think_content = thinkContent
                msg.content = data.content
                msg.is_streaming = false
              }
              await saveConversations()
            } else if (data.type === 'error') {
              ElMessage.error(data.content)
              const msg = messages.value.find(m => m.id === assistantMsgId)
              if (msg) {
                msg.is_streaming = false
              }
            }
          } catch (e) {
            console.error('Parse error:', e)
          }
        }
      }
    }

    if (thinkContent) {
      ElMessage.success('深度思考完成')
    }

    extractedFeatures.value = []
    scrollToBottom()
  } catch (e) {
    ElMessage.error('发送失败：' + e.message)
    const msg = messages.value.find(m => m.is_streaming)
    if (msg) {
      msg.is_streaming = false
      msg.content = '抱歉，响应时出现错误：' + e.message
    }
  } finally {
    loading.value = false
  }
}

async function saveConversations() {
  try {
    const conversationData = messages.value
      .filter(msg => msg.role === 'user' || (msg.role === 'assistant' && !msg.is_streaming))
      .map(msg => ({
        role: msg.role,
        content: msg.content
      }))
    
    localStorage.setItem(`chat_${userId.value}`, JSON.stringify(conversationData))
  } catch (e) {
    console.error('保存对话失败:', e)
  }
}

function changeUser() {
  store.setUserId(userId.value)
  messages.value = []
  extractedFeatures.value = []
  loadLocalConversations()
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

function renderMarkdown(content) {
  if (!content) return ''
  return md.render(content)
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
  gap: 12px;
}

.user-input {
  width: 200px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
}

.messages-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  animation: messageIn 0.3s ease;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.avatar-circle.assistant {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}

.avatar-circle.user {
  background: linear-gradient(135deg, #22c55e, #10b981);
  color: white;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-width: 70%;
}

.message.user .message-content {
  align-items: flex-end;
}

.message-bubble {
  background: var(--bg-tertiary);
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.message.user .message-bubble {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}

.message-text {
  line-height: 1.6;
  word-wrap: break-word;
}

.markdown-content {
  white-space: pre-wrap;
  line-height: 1.6;
}

.markdown-content :deep(p) {
  margin: 0.5em 0;
  line-height: 1.6;
}

.markdown-content :deep(ol), .markdown-content :deep(ul) {
  padding-left: 2em;
  margin: 0.5em 0;
}

.markdown-content :deep(li) {
  margin: 0.3em 0;
  line-height: 1.6;
}

.markdown-content :deep(ol li), .markdown-content :deep(ul li) {
  display: list-item;
}

.markdown-content :deep(strong) {
  font-weight: 600;
}

.markdown-content :deep(code) {
  background: var(--bg-tertiary);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background: var(--bg-primary);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid var(--accent-color);
  padding-left: 16px;
  margin: 8px 0;
  color: var(--text-secondary);
}

.message-time {
  font-size: 12px;
  color: var(--text-muted);
}

.think-content {
  margin-bottom: 12px;
}

.think-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  padding: 8px;
  background: var(--bg-primary);
  border-radius: 8px;
}

.loading-dots {
  display: flex;
  gap: 4px;
  align-items: center;
  height: 20px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: var(--accent-color);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.chat-input-area {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.think-btn {
  flex-shrink: 0;
}

.think-btn.active {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}

.message-input {
  flex: 1;
}

.message-input :deep(.el-textarea__inner) {
  resize: none;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
}

.send-btn {
  flex-shrink: 0;
}

.features-panel {
  width: 320px;
  background: var(--bg-secondary);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--text-primary);
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
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 10px;
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

.message-enter-active,
.message-leave-active {
  transition: all 0.3s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.message-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
