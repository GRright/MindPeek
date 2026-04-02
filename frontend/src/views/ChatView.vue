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

                <div v-if="msg.images && msg.images.length > 0" class="message-images">
                  <img v-for="(img, idx) in msg.images" :key="idx" :src="img" alt="图片" @click="previewImage(img)" />
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
          <div class="input-tools">
            <button class="tool-btn">
              <el-icon><Paperclip /></el-icon>
            </button>
            <button
              v-if="store.multimodalEnabled"
              class="tool-btn"
              @click="triggerImageUpload"
            >
              <el-icon><Picture /></el-icon>
            </button>
            <input
              ref="imageInput"
              type="file"
              accept="image/*"
              style="display: none"
              @change="handleImageSelect"
            />
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

          <div v-if="uploadedImages.length > 0" class="uploaded-images-preview">
            <div v-for="img in uploadedImages" :key="img.id" class="uploaded-image-item">
              <img :src="img.url" :alt="img.name" />
              <button class="remove-image-btn" @click="removeImage(img.id)">
                <el-icon><Close /></el-icon>
              </button>
            </div>
          </div>

          <div class="send-section">
            <button
              class="send-btn"
              :class="{ loading: loading }"
              @click="sendMessage"
              :disabled="loading || (!inputMessage.trim() && uploadedImages.length === 0)"
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
import { ref, computed, onMounted, nextTick } from 'vue'
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
  ArrowDown,
  Close
} from '@element-plus/icons-vue'

const store = useProfileStore()
const md = new MarkdownIt()

const userId = computed(() => store.currentUserId)
const inputMessage = ref('')
const messages = ref([])
const loading = ref(false)
const messagesContainer = ref(null)
const inputTextarea = ref(null)
const imageInput = ref(null)
const uploadedImages = ref([])

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

function triggerImageUpload() {
  imageInput.value?.click()
}

async function handleImageSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    return
  }

  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过 10MB')
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImages.value.push({
      id: Date.now(),
      url: e.target.result,
      name: file.name
    })
    ElMessage.success('图片已上传，将随消息发送')
  }
  reader.readAsDataURL(file)
  event.target.value = ''
}

function removeImage(imageId) {
  uploadedImages.value = uploadedImages.value.filter(img => img.id !== imageId)
}

function previewImage(url) {
  window.open(url, '_blank')
}

function copyMessage(content) {
  console.log('复制消息:', content)
  navigator.clipboard.writeText(content)
    .then(() => {
      ElMessage.success('已复制到剪贴板')
    })
    .catch((err) => {
      console.error('复制失败:', err)
      ElMessage.error('复制失败，请手动复制')
    })
}

function regenerateMessage(msg) {
  console.log('重新生成消息:', msg)
  if (msg.role === 'assistant') {
    const userMsg = messages.value.slice().reverse().find(m => m.role === 'user' && m.id < msg.id)
    console.log('找到用户消息:', userMsg)
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
  nextTick(() => {
    scrollToBottom()
  })
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
    scrollToBottom()
  } catch (e) {
    console.error('加载本地对话失败:', e)
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
}

async function sendMessage() {
  if ((!inputMessage.value.trim() && uploadedImages.value.length === 0) || loading.value) {
    return
  }

  const message = inputMessage.value
  const images = [...uploadedImages.value]
  inputMessage.value = ''
  uploadedImages.value = []
  if (inputTextarea.value) {
    inputTextarea.value.style.height = 'auto'
  }

  const userMsgId = Date.now()
  const userMessage = {
    id: userMsgId,
    role: 'user',
    content: message,
    images: images.map(img => img.url),
    timestamp: new Date().toISOString()
  }
  messages.value.push(userMessage)

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
        extract_features: true,
        images: images.length > 0 ? images.map(img => img.url) : null
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
              loading.value = false
              await saveConversations()
              break
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
      const container = messagesContainer.value
      const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100
      if (isNearBottom) {
        container.scrollTop = container.scrollHeight
      }
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
  gap: 0.625rem;
  margin-bottom: 0.75rem;
}

.message-author {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
}

.message-time {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.message-body {
  font-size: 0.9375rem;
  line-height: 1.8;
  color: var(--text-primary);
}

.thinking-box {
  margin-bottom: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--bg-tertiary);
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.625rem 0.875rem;
  background: var(--bg-hover);
  cursor: pointer;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: background 0.15s ease;
}

.thinking-header:hover {
  background: var(--bg-tertiary);
}

.thinking-body {
  padding: 0.875rem;
  font-size: 0.875rem;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.message-text {
  font-size: 0.9375rem;
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
  border-radius: 0.25rem;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
  color: #ec4899;
}

.message-text :deep(pre) {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  padding: 1rem;
  border-radius: 0.5rem;
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
  gap: 0.3125rem;
  padding: 0.625rem 0;
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
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.message-actions {
  display: flex;
  gap: 0.25rem;
  margin-top: 0.75rem;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.message:hover .message-actions {
  opacity: 1;
}

.message-action-btn {
  width: 1.875rem;
  height: 1.875rem;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 0.375rem;
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
  padding: 1.25rem;
  background: var(--bg-primary);
}

.input-container {
  max-width: 50rem;
  margin: 0 auto;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 1rem;
  display: flex;
  align-items: flex-end;
  overflow: hidden;
  transition: border-color 0.15s ease;
}

.input-container:focus-within {
  border-color: var(--accent-color);
}

.uploaded-images-preview {
  display: flex;
  gap: 8px;
  padding: 0 12px;
  flex-wrap: wrap;
}

.uploaded-image-item {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 8px;
  overflow: hidden;
}

.uploaded-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.message-images {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.message-images img {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  cursor: pointer;
  object-fit: cover;
  transition: transform 0.2s ease;
}

.message-images img:hover {
  transform: scale(1.05);
}

.remove-image-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.remove-image-btn:hover {
  background: rgba(239, 68, 68, 0.8);
}

.input-tools {
  display: flex;
  padding: 0.75rem 0.5rem;
}

.tool-btn {
  width: 2.25rem;
  height: 2.25rem;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: 0.5rem;
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
  padding: 0.75rem 0;
}

.textarea-wrapper textarea {
  width: 100%;
  border: none;
  background: transparent;
  resize: none;
  font-size: 0.9375rem;
  font-family: inherit;
  color: var(--text-primary);
  line-height: 1.6;
  padding: 0 0 0 0.5rem;
  min-height: 1.5rem;
  max-height: 12.5rem;
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
  padding: 0.75rem 0.75rem 0.75rem 0.5rem;
}

.send-btn {
  width: 2.25rem;
  height: 2.25rem;
  border: none;
  border-radius: 0.5rem;
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
  max-width: 50rem;
  margin: 0.5rem auto 0;
  text-align: center;
}

.input-footer-text span {
  font-size: 0.75rem;
  color: var(--text-muted);
}

@media screen and (max-width: 768px) {
  .chat-view {
    height: calc(100vh - 5rem);
    min-height: 300px;
  }
  
  .message {
    padding: 1rem 1rem;
    gap: 0.75rem;
  }
  
  .welcome-content {
    padding: 1.5rem;
  }
  
  .welcome-content h1 {
    font-size: 1.5rem;
  }
  
  .welcome-content p {
    font-size: 0.875rem;
  }
  
  .welcome-logo {
    width: 4rem;
    height: 4rem;
  }
  
  .input-area {
    padding: 0.75rem;
  }
  
  .input-container {
    border-radius: 0.75rem;
  }
}

@media screen and (min-width: 1920px) {
  .chat-view {
    max-width: 1400px;
    margin: 0 auto;
  }
}
</style>
