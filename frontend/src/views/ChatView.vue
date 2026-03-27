<template>
  <div class="chat-view">
    <div class="chat-area">
      <div class="messages-area" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome-screen">
          <div class="welcome-content">
            <div class="welcome-logo">
              <el-icon :size="64"><ChatDotRound /></el-icon>
            </div>
            <h1>MindPeek AI</h1>
            <p>懂你的 AI 伙伴，通过对话自动理解你</p>
          </div>
        </div>

        <div class="messages-list" v-else>
          <div
            v-for="msg in messages"
            :key="msg.id"
            :class="['message', msg.role]"
          >
            <div class="message-avatar">
              <div class="avatar" :class="msg.role">
                <el-icon v-if="msg.role === 'user'"><User /></el-icon>
                <el-icon v-else><Cpu /></el-icon>
              </div>
            </div>

            <div class="message-content">
              <div class="message-header">
                <span class="message-author">{{ msg.role === 'user' ? '用户' : 'MindPeek' }}</span>
                <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
              </div>

              <div class="message-body">
                <div v-if="msg.think_content && !msg.is_streaming" class="thinking-box">
                  <div class="thinking-header" @click="msg.showThinking = !msg.showThinking">
                    <el-icon v-if="!msg.showThinking"><ArrowRight /></el-icon>
                    <el-icon v-else><ArrowDown /></el-icon>
                    <span>深度思考</span>
                  </div>
                  <div v-show="msg.showThinking" class="thinking-body">
                    {{ formatThinkContent(msg.think_content) }}
                  </div>
                </div>

                <div v-if="msg.content" v-html="renderMarkdown(msg.content)" class="message-text"></div>

                <div v-if="msg.is_streaming" class="typing-dots">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>

              <div class="message-actions">
                <button class="message-action-btn" @click="copyMessage(msg.content)">
                  <el-icon><DocumentCopy /></el-icon>
                </button>
                <button class="message-action-btn" @click="regenerateMessage(msg)">
                  <el-icon><Refresh /></el-icon>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-container">
          <div class="input-tools">
            <button class="tool-btn">
              <el-icon><Paperclip /></el-icon>
            </button>
            <button class="tool-btn">
              <el-icon><Picture /></el-icon>
            </button>
          </div>

          <div class="textarea-wrapper">
            <textarea
              v-model="inputMessage"
              placeholder="发送消息给 MindPeek..."
              :rows="1"
              :disabled="loading"
              @keydown.enter.exact.prevent="sendMessage"
              @input="autoResize"
              ref="inputTextarea"
            ></textarea>
          </div>

          <div class="send-section">
            <button
              class="send-btn"
              :class="{ loading: loading }"
              @click="sendMessage"
              :disabled="loading || !inputMessage.trim()"
            >
              <el-icon v-if="!loading"><Promotion /></el-icon>
              <el-icon v-else class="spinner-icon"><Loading /></el-icon>
            </button>
          </div>
        </div>

        <div class="input-footer-text">
          <span>MindPeek 可能会出错，请仔细检查重要信息</span>
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
  Paperclip,
  Picture,
  Refresh,
  DocumentCopy,
  ArrowRight,
  ArrowDown
} from '@element-plus/icons-vue'

const store = useProfileStore()
const md = new MarkdownIt()

const userId = ref(store.currentUserId)
const inputMessage = ref('')
const messages = ref([])
const loading = ref(false)
const messagesContainer = ref(null)
const inputTextarea = ref(null)

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

function clearChat() {
  messages.value = []
  saveConversations()
}

function sendSuggestion(text) {
  inputMessage.value = text
  sendMessage()
}

function copyMessage(content) {
  navigator.clipboard.writeText(content)
  ElMessage.success('已复制到剪贴板')
}

function regenerateMessage(msg) {
  if (msg.role === 'assistant') {
    const userMsg = messages.value.slice().reverse().find(m => m.role === 'user' && m.id < msg.id)
    if (userMsg) {
      const msgIndex = messages.value.findIndex(m => m.id === msg.id)
      if (msgIndex > -1) {
        messages.value.splice(msgIndex, 1)
      }
      inputMessage.value = userMsg.content
      sendMessage()
    }
  }
}

onMounted(async () => {
  await loadLocalConversations()
  nextTick(() => {
    scrollToBottom()
  })
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
        showThinking: false,
        timestamp: new Date().toISOString()
      }))
    }
    scrollToBottom()
  } catch (e) {
    console.error('加载本地对话失败:', e)
  }
}

async function sendMessage() {
  if (!inputMessage.value.trim() || loading.value) {
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
      showThinking: false,
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
        extract_features: true
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
    loading.value = false

    if (thinkContent) {
      ElMessage.success('深度思考完成')
    }

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
        content: msg.content,
        think_content: msg.think_content
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
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
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
  height: calc(100vh - 112px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.messages-area::-webkit-scrollbar {
  width: 8px;
}

.messages-area::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

.messages-area::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border-radius: 4px;
}

.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-content {
  text-align: center;
  max-width: 700px;
  padding: 40px;
}

.welcome-logo {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 24px;
}

.welcome-content h1 {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.welcome-content p {
  font-size: 16px;
  color: var(--text-muted);
  margin: 0 0 40px;
}

.messages-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px 0;
}

.message {
  display: flex;
  gap: 20px;
  padding: 24px 60px;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
}

.message.user {
  background: transparent;
}

.message.assistant {
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  border-bottom: 1px solid var(--border-color);
}

.message-avatar {
  flex-shrink: 0;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.avatar.user {
  background: linear-gradient(135deg, #10b981, #059669);
}

.avatar.assistant {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.message-author {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.message-time {
  font-size: 12px;
  color: var(--text-muted);
}

.message-body {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-primary);
}

.thinking-box {
  margin-bottom: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-tertiary);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: var(--bg-hover);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: background 0.15s ease;
}

.thinking-header:hover {
  background: var(--bg-tertiary);
}

.thinking-body {
  padding: 14px;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.message-text {
  font-size: 15px;
  line-height: 1.8;
}

.message-text :deep(p) {
  margin: 0;
}

.message-text :deep(p + p) {
  margin-top: 1em;
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
  color: var(--text-primary);
}

.message-text :deep(code) {
  background: var(--bg-tertiary);
  padding: 0.2em 0.5em;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
  color: #ec4899;
}

.message-text :deep(pre) {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.message-text :deep(pre code) {
  background: transparent;
  padding: 0;
  color: var(--text-primary);
}

.typing-dots {
  display: flex;
  gap: 5px;
  padding: 10px 0;
}

.typing-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-dots .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-dots .dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 12px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.message:hover .message-actions {
  opacity: 1;
}

.message-action-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.message-action-btn:hover {
  border-color: var(--border-color);
  background: var(--bg-hover);
  color: var(--text-primary);
}

.input-area {
  flex-shrink: 0;
  padding: 20px;
  background: var(--bg-primary);
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
  transition: border-color 0.15s ease;
}

.input-container:focus-within {
  border-color: var(--accent-color);
}

.input-tools {
  display: flex;
  padding: 12px 8px;
}

.tool-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.tool-btn:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}

.textarea-wrapper {
  flex: 1;
  padding: 12px 0;
}

.textarea-wrapper textarea {
  width: 100%;
  border: none;
  background: transparent;
  resize: none;
  font-size: 15px;
  font-family: inherit;
  color: var(--text-primary);
  line-height: 1.6;
  padding: 0;
  min-height: 24px;
  max-height: 200px;
  overflow-y: auto;
}

.textarea-wrapper textarea::placeholder {
  color: var(--text-muted);
}

.textarea-wrapper textarea:focus {
  outline: none;
}

.send-section {
  display: flex;
  padding: 12px 12px 12px 8px;
}

.send-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: var(--accent-color);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn.loading {
  background: var(--text-muted);
}

.spinner-icon {
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

.input-footer-text {
  max-width: 800px;
  margin: 8px auto 0;
  text-align: center;
}

.input-footer-text span {
  font-size: 12px;
  color: var(--text-muted);
}
</style>
