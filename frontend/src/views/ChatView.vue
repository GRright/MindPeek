<template>
  <div class="chat-view">
    <div class="chat-area">
      <div class="messages-area" ref="messagesContainer" @scroll="handleUserScroll">
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
                <img v-if="msg.role === 'assistant'" :src="logo" alt="MindPeek" class="avatar-logo" />
                <el-icon v-else-if="msg.role === 'user'"><User /></el-icon>
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
                <button class="message-action-btn" @click.stop="copyMessage(msg.content)">
                  <el-icon><DocumentCopy /></el-icon>
                </button>
                <button class="message-action-btn" @click.stop="regenerateMessage(msg)">
                  <el-icon><Refresh /></el-icon>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-container">
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
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useProfileStore } from '@/stores/profile'
import MarkdownIt from 'markdown-it'
import logo from '@/assets/logo.png'
import {
  User,
  ChatDotRound,
  Promotion,
  Loading,
  Refresh,
  DocumentCopy,
  ArrowRight,
  ArrowDown
} from '@element-plus/icons-vue'

const store = useProfileStore()
const md = new MarkdownIt()

const userId = computed(() => store.currentUserId)
const inputMessage = ref('')
const messages = ref([])
const loading = ref(false)
const messagesContainer = ref(null)
const inputTextarea = ref(null)
const userScrolledUp = ref(false)

function handleUserScroll() {
  if (!messagesContainer.value) return
  const container = messagesContainer.value
  const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
  userScrolledUp.value = !isNearBottom
}

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
    .then(() => {
      ElMessage.success('已复制到剪贴板')
    })
    .catch(() => {
      ElMessage.error('复制失败，请手动复制')
    })
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
    } else {
      ElMessage.warning('找不到对应的用户消息')
    }
  } else {
    ElMessage.warning('只能重新生成助手的回复')
  }
}

onMounted(async () => {
  await loadLocalConversations()
})

onUnmounted(() => {
  loading.value = false
})

async function loadLocalConversations() {
  try {
    const conversations = await store.loadConversations(50)
    if (conversations && conversations.length > 0) {
      messages.value = conversations.map((msg, idx) => ({
        id: Date.now() + idx,
        role: msg.role,
        content: msg.content,
        think_content: msg.think_content || '',
        is_streaming: false,
        showThinking: false,
        timestamp: msg.timestamp || new Date().toISOString()
      }))
      saveConversations()
    } else {
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
    }
  } catch (e) {
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
  }
  scrollToBottom(true)
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

  userScrolledUp.value = false
  scrollToBottom(true)

  loading.value = true
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

  let fullResponse = ''
  let thinkContent = null
  let streamEnded = false

  try {
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
    let buffer = ''

    while (!streamEnded) {
      const { done, value } = await reader.read()
      
      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const jsonStr = line.substring(6).trim()
          if (!jsonStr) continue
          
          try {
            const data = JSON.parse(jsonStr)
            
            if (data.type === 'chunk') {
              fullResponse += data.content
              const msg = messages.value.find(m => m.id === assistantMsgId)
              if (msg) {
                msg.content = fullResponse
              }
              scrollToBottom(false)
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
                msg.content = data.content || fullResponse
                msg.is_streaming = false
              }
              streamEnded = true
              break
            } else if (data.type === 'error') {
              ElMessage.error(data.content)
              const msg = messages.value.find(m => m.id === assistantMsgId)
              if (msg) {
                msg.is_streaming = false
                msg.content = '抱歉，AI服务暂时不可用'
              }
              streamEnded = true
              break
            }
          } catch (parseErr) {
            console.warn('Parse error:', parseErr)
          }
        }
      }
    }
  } catch (err) {
    if (err.name === 'AbortError' || err.message.includes('abort')) {
      console.log('Request aborted')
    } else {
      console.error('Stream error:', err)
      ElMessage.error('发送失败：' + err.message)
      const msg = messages.value.find(m => m.id === assistantMsgId)
      if (msg) {
        msg.is_streaming = false
        msg.content = '抱歉，响应时出现错误'
      }
    }
  } finally {
    loading.value = false
    
    const msg = messages.value.find(m => m.id === assistantMsgId)
    if (msg) {
      msg.is_streaming = false
      if (!msg.content) {
        msg.content = fullResponse || '响应已完成'
      }
    }
    
    await saveConversations()
    
    if (thinkContent) {
      ElMessage.success('深度思考完成')
    }
    
    scrollToBottom(false)
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

function scrollToBottom(force = false) {
  nextTick(() => {
    if (!messagesContainer.value) return
    
    if (force || !userScrolledUp.value) {
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
  height: calc(100vh - 7rem);
  min-height: 400px;
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
  width: 0.5rem;
}

.messages-area::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

.messages-area::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border-radius: 0.25rem;
}

.welcome-screen {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-content {
  text-align: center;
  max-width: 43.75rem;
  padding: 2.5rem;
}

.welcome-logo {
  width: 5rem;
  height: 5rem;
  border-radius: 1.25rem;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 1.5rem;
}

.welcome-content h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.5rem;
}

.welcome-content p {
  font-size: 1rem;
  color: var(--text-muted);
  margin: 0 0 2.5rem;
}

.messages-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 1.5rem 0;
}

.message {
  display: flex;
  gap: 1.25rem;
  padding: 1.5rem 3.75rem;
  max-width: 62.5rem;
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
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.375rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1rem;
}

.avatar-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 0.375rem;
}

.avatar.user {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
}

.avatar.assistant {
  background: transparent;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.message-author {
  font-weight: 600;
  color: var(--text-primary);
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.message-body {
  color: var(--text-primary);
  line-height: 1.6;
}

.message-text {
  word-wrap: break-word;
}

.message-text :deep(p) {
  margin: 0 0 1rem;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(code) {
  background: var(--bg-tertiary);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
}

.message-text :deep(pre) {
  background: var(--bg-tertiary);
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
}

.thinking-box {
  background: var(--bg-tertiary);
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  overflow: hidden;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.thinking-header:hover {
  color: var(--text-primary);
}

.thinking-body {
  padding: 0 1rem 1rem;
  color: var(--text-muted);
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

.typing-dots {
  display: flex;
  gap: 0.25rem;
  padding: 0.5rem 0;
}

.typing-dots .dot {
  width: 0.5rem;
  height: 0.5rem;
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
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.message-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.message:hover .message-actions {
  opacity: 1;
}

.message-action-btn {
  background: var(--bg-tertiary);
  border: none;
  border-radius: 0.375rem;
  padding: 0.375rem;
  cursor: pointer;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.message-action-btn:hover {
  background: var(--bg-primary);
  color: var(--text-primary);
}

.input-area {
  padding: 1rem 3.75rem 1.5rem;
  max-width: 62.5rem;
  margin: 0 auto;
  width: 100%;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 0.75rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 1rem;
  padding: 0.75rem 1rem;
}

.textarea-wrapper {
  flex: 1;
}

.textarea-wrapper textarea {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 1rem;
  line-height: 1.5;
  resize: none;
  outline: none;
  font-family: inherit;
  max-height: 12.5rem;
}

.textarea-wrapper textarea::placeholder {
  color: var(--text-muted);
}

.textarea-wrapper textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-section {
  flex-shrink: 0;
}

.send-btn {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  border: none;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.send-btn.loading {
  background: var(--bg-tertiary);
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
  text-align: center;
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

@media (max-width: 48rem) {
  .message {
    padding: 1rem 1.5rem;
  }

  .input-area {
    padding: 1rem 1.5rem 1.5rem;
  }
}
</style>
