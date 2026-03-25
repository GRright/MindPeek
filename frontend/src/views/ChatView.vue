<template>
  <div class="chat-view">
    <div class="chat-header">
      <div class="header-content">
        <div class="logo">
          <el-icon :size="24"><ChatDotRound /></el-icon>
          <span class="title">MindPeek Chat</span>
        </div>
        <div class="user-selector">
          <el-icon :size="16"><User /></el-icon>
          <span class="user-name">{{ userId }}</span>
        </div>
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">
          <el-icon :size="64"><ChatDotRound /></el-icon>
        </div>
        <h3>开始对话</h3>
        <p>发送消息开始分析用户特征</p>
      </div>

      <div class="messages-container">
        <div
          v-for="msg in messages"
          :key="msg.id"
          :class="['message-row', msg.role]"
        >
          <div class="avatar">
            <div class="avatar-icon">
              <el-icon v-if="msg.role === 'user'" :size="20"><User /></el-icon>
              <el-icon v-else :size="20"><Cpu /></el-icon>
            </div>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <div v-if="msg.think_content && !msg.is_streaming" class="think-content">
                <el-collapse v-model="msg.activeCollapse" accordion>
                  <el-collapse-item :name="msg.id">
                    <template #title>
                      <span class="think-title">💭 深度思考</span>
                    </template>
                    <div class="think-text">{{ formatThinkContent(msg.think_content) }}</div>
                  </el-collapse-item>
                </el-collapse>
              </div>
              <div v-if="msg.content" v-html="renderMarkdown(msg.content)" class="message-text"></div>
              <div v-if="msg.is_streaming" class="loading">
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
                <span class="loading-dot"></span>
              </div>
            </div>
            <div class="message-meta">
              <span class="time">{{ formatTime(msg.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input">
      <div class="input-container">
        <div class="input-actions">
          <el-tooltip content="深度思考">
            <button
              class="action-btn"
              :class="{ active: deepThink }"
              @click="deepThink = !deepThink"
              :disabled="loading"
            >
              <el-icon :size="18"><MagicStick /></el-icon>
            </button>
          </el-tooltip>
        </div>
        <div class="input-wrapper">
          <textarea
            v-model="inputMessage"
            placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
            :rows="1"
            :disabled="loading"
            @keydown.enter.exact.prevent="sendMessage"
            @input="autoResize"
            ref="inputTextarea"
          ></textarea>
          <button
            class="send-btn"
            @click="sendMessage"
            :disabled="loading || !inputMessage.trim()"
          >
            <el-icon v-if="!loading" :size="20"><Promotion /></el-icon>
            <el-icon v-else class="is-loading" :size="20"><Loading /></el-icon>
          </button>
        </div>
      </div>
    </div>
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
const inputTextarea = ref(null)
const deepThink = ref(false)

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
    scrollToBottom()
  } catch (e) {
    console.error('加载本地对话失败:', e)
  }
}

async function sendMessage() {
  console.log('sendMessage called, loading:', loading.value)
  if (!inputMessage.value.trim() || loading.value) {
    console.log('Early return: empty message or loading')
    return
  }

  const message = inputMessage.value
  inputMessage.value = ''
  if (inputTextarea.value) {
    inputTextarea.value.style.height = 'auto'
  }

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
  console.log('Set loading to true')
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

    const response = await fetch('/api/stream', {
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
                msg.content = '抱歉，AI服务暂时不可用'
              }
              loading.value = false
            }
          } catch (e) {
            console.error('Parse error:', e)
          }
        }
      }
    }
    console.log('Stream complete, setting loading to false')
    loading.value = false

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
    console.log('Set loading to false in finally')
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

    const refreshEvent = new CustomEvent('profileNeedsRefresh', { detail: { userId: userId.value } })
    window.dispatchEvent(refreshEvent)
  } catch (e) {
    console.error('保存对话失败:', e)
  }
}

function autoResize(e) {
  const textarea = e.target
  textarea.style.height = 'auto'
  textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
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
</script>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-primary);
}

.chat-header {
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: 12px 20px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--accent-color);
}

.logo .title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.user-selector {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-muted);
  text-align: center;
}

.empty-icon {
  opacity: 0.3;
  margin-bottom: 20px;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.empty-state p {
  font-size: 14px;
}

.messages-container {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-row {
  display: flex;
  gap: 16px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  flex-shrink: 0;
}

.avatar-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.message-row.assistant .avatar-icon {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}

.message-row.user .avatar-icon {
  background: linear-gradient(135deg, #22c55e, #10b981);
  color: white;
}

.message-content {
  flex: 1;
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message-row.user .message-content {
  align-items: flex-end;
}

.message-bubble {
  padding: 14px 18px;
  border-radius: 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  line-height: 1.5;
}

.message-row.user .message-bubble {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}

.message-text {
  font-size: 15px;
}

.message-text :deep(p) {
  margin: 0;
}

.message-text :deep(p + p) {
  margin-top: 0.5em;
}

.message-text :deep(ol), .message-text :deep(ul) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.message-text :deep(li) {
  margin: 0.3em 0;
}

.message-text :deep(strong) {
  font-weight: 600;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 0.15em 0.4em;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}

.message-text :deep(pre) {
  background: rgba(0, 0, 0, 0.05);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 4px;
}

.time {
  font-size: 12px;
  color: var(--text-muted);
}

.think-content {
  margin-bottom: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.think-title {
  font-size: 13px;
  font-weight: 500;
}

.think-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  padding: 8px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 6px;
  white-space: pre-wrap;
}

.loading {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
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

.chat-input {
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  padding: 16px 20px;
}

.input-container {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.action-btn:hover {
  border-color: var(--accent-color);
  color: var(--accent-color);
}

.action-btn.active {
  background: var(--accent-color);
  border-color: var(--accent-color);
  color: white;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-wrapper {
  flex: 1;
  display: flex;
  gap: 10px;
  align-items: center;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 4px 4px 4px 16px;
  transition: border-color 0.2s ease;
  min-height: 40px;
}

.input-wrapper:focus-within {
  border-color: var(--accent-color);
}

.input-wrapper textarea {
  flex: 1;
  border: none;
  background: transparent;
  resize: none;
  font-size: 15px;
  font-family: inherit;
  color: var(--text-primary);
  line-height: 1.5;
  padding: 8px 0;
  min-height: 24px;
  max-height: 120px;
  overflow-y: auto;
  vertical-align: middle;
}

.input-wrapper textarea::placeholder {
  color: var(--text-muted);
  vertical-align: middle;
  line-height: 1.5;
}

.input-wrapper textarea:focus {
  outline: none;
}

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  border: none;
  background: var(--accent-color);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
