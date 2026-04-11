<template>
  <div class="chat-view">
    <div class="chat-container">
      <div class="messages-section" ref="messagesScroll" @scroll="handleScroll">
        <div v-if="messages.length === 0" class="hero-welcome">
          <div class="welcome-stage">
            <div class="hero-logo">
              <div class="logo-orb orb-1"></div>
              <div class="logo-orb orb-2"></div>
              <div class="logo-orb orb-3"></div>
              <div class="logo-center">
                <img :src="logo" alt="MindPeek" class="logo-image" />
              </div>
            </div>
            
            <div class="hero-text">
              <h1 class="hero-title">
                欢迎来到
                <span class="gradient-text">MindPeek</span>
              </h1>
              <p class="hero-subtitle">
                通过持续对话，让 AI 真正理解你的个性、习惯与偏好
              </p>
            </div>
            
            <div class="feature-cards">
              <div class="feature-card" v-for="(feature, i) in features" :key="i" :style="{ animationDelay: `${i * 0.1}s` }">
                <div class="feature-icon">{{ feature.icon }}</div>
                <div class="feature-content">
                  <h3>{{ feature.title }}</h3>
                  <p>{{ feature.desc }}</p>
                </div>
              </div>
            </div>
            
            <div class="quick-actions">
              <button 
                v-for="(suggestion, index) in suggestions" 
                :key="index" 
                class="action-button"
                @click="sendSuggestion(suggestion)"
                :style="{ animationDelay: `${index * 0.08}s` }"
              >
                <div class="button-glow"></div>
                <span class="button-text">{{ suggestion }}</span>
                <div class="button-arrow">
                  <el-icon><Promotion /></el-icon>
                </div>
              </button>
            </div>
          </div>
        </div>

        <div v-else class="messages-list">
          <div v-for="msg in messages" :key="msg.id" :class="['message-card', msg.role]">
            <div class="message-avatar">
              <div :class="['avatar-circle', msg.role]">
                <img v-if="msg.role === 'assistant'" :src="logo" class="avatar-img" />
                <el-icon v-else><User /></el-icon>
              </div>
            </div>
            
            <div class="message-bubble">
              <div class="message-header">
                <span class="sender-name">{{ msg.role === 'user' ? '你' : 'MindPeek' }}</span>
                <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
              </div>
              
              <div v-if="msg.think_content && !msg.is_streaming" class="thinking-box">
                <div class="thinking-toggle" @click="msg.showThinking = !msg.showThinking">
                  <div class="thinking-icon">
                    <el-icon v-if="!msg.showThinking"><ArrowRight /></el-icon>
                    <el-icon v-else><ArrowDown /></el-icon>
                  </div>
                  <span>深度思考</span>
                  <span class="thinking-emoji">🤔</span>
                </div>
                <div v-show="msg.showThinking" class="thinking-content">
                  <p>{{ msg.think_content }}</p>
                </div>
              </div>
              
              <div class="message-content">
                <div v-if="msg.content" v-html="renderMarkdown(msg.content)" class="message-text"></div>
                <div v-if="msg.is_streaming" class="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
              
              <div class="message-actions" v-if="msg.role === 'assistant' && !msg.is_streaming">
                <button class="action-link" @click="copyMessage(msg.content)">
                  <el-icon><DocumentCopy /></el-icon>
                  <span>复制</span>
                </button>
                <button class="action-link" @click="regenerateMessage(msg)">
                  <el-icon><Refresh /></el-icon>
                  <span>重新生成</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-wrapper">
          <div class="input-field">
            <textarea
              v-model="inputMessage"
              placeholder="开始你的对话..."
              :rows="1"
              :disabled="loading"
              @keydown.enter.exact.prevent="handleSend"
              @input="autoResize"
              ref="textareaRef"
              class="chat-textarea"
            ></textarea>
          </div>
          <button class="send-btn" @click="handleSend" :disabled="loading || !inputMessage.trim()">
            <div class="send-inner">
              <el-icon v-if="!loading"><Promotion /></el-icon>
              <el-icon v-else class="spinner"><Loading /></el-icon>
            </div>
          </button>
        </div>
        <div class="input-tip">
          <span class="tip-icon">💡</span>
          <span>提示：越详细的对话，MindPeek 越能深入了解你</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'
import { useProfileStore } from '@/stores/profile'
import MarkdownIt from 'markdown-it'
import { ElMessage } from 'element-plus'
import logo from '@/assets/logo.png'
import {
  User,
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
const messagesScroll = ref(null)
const textareaRef = ref(null)
const userScrolled = ref(false)

const features = [
  { icon: '🧠', title: '深度理解', desc: 'AI 会持续学习你的偏好与习惯' },
  { icon: '🎯', title: '精准分析', desc: '构建完整的个人特征图谱' },
  { icon: '✨', title: '个性化体验', desc: '每一次对话都让 AI 更了解你' }
]

const suggestions = [
  '介绍一下你自己',
  '帮我分析一下我的性格',
  '我喜欢在周末看书',
  '给我一些生活建议'
]

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
    } else {
      const saved = localStorage.getItem(`chat_${userId.value}`)
      if (saved) {
        messages.value = JSON.parse(saved)
      }
    }
  } catch (e) {
    console.error('加载对话失败:', e)
  }
  scrollToBottom(true)
}

function handleScroll() {
  if (!messagesScroll.value) return
  const container = messagesScroll.value
  const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 150
  userScrolled.value = !isNearBottom
}

function autoResize(e) {
  const textarea = e.target
  textarea.style.height = 'auto'
  textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px'
}

async function handleSend() {
  if (!inputMessage.value.trim() || loading.value) return
  await sendMessage(inputMessage.value)
}

async function sendMessage(text) {
  const message = text
  inputMessage.value = ''
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }

  const userMsgId = Date.now()
  messages.value.push({
    id: userMsgId,
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  })

  userScrolled.value = false
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

  try {
    const response = await fetch('/api/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId.value,
        message: message,
        extract_features: true
      })
    })

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const jsonStr = line.substring(6).trim()
        if (!jsonStr) continue

        try {
          const data = JSON.parse(jsonStr)
          if (data.type === 'chunk') {
            fullResponse += data.content
            const msg = messages.value.find(m => m.id === assistantMsgId)
            if (msg) msg.content = fullResponse
            scrollToBottom(false)
          } else if (data.type === 'think' && data.content) {
            thinkContent = data.content
            const msg = messages.value.find(m => m.id === assistantMsgId)
            if (msg) msg.think_content = thinkContent
          } else if (data.type === 'done') {
            thinkContent = data.think_content
            const msg = messages.value.find(m => m.id === assistantMsgId)
            if (msg) {
              msg.think_content = thinkContent
              msg.content = data.content || fullResponse
              msg.is_streaming = false
            }
            break
          } else if (data.type === 'error') {
            ElMessage.error(data.content)
            const msg = messages.value.find(m => m.id === assistantMsgId)
            if (msg) {
              msg.is_streaming = false
              msg.content = '抱歉，AI服务暂时不可用'
            }
            break
          }
        } catch (e) {
          console.warn('Parse error:', e)
        }
      }
    }
  } catch (err) {
    console.error('Stream error:', err)
    ElMessage.error('发送失败：' + err.message)
    const msg = messages.value.find(m => m.id === assistantMsgId)
    if (msg) {
      msg.is_streaming = false
      msg.content = '抱歉，响应时出现错误'
    }
  } finally {
    loading.value = false
    const msg = messages.value.find(m => m.id === assistantMsgId)
    if (msg) {
      msg.is_streaming = false
      if (!msg.content) msg.content = fullResponse || '响应已完成'
    }
    await saveConversations()
    scrollToBottom(false)
  }
}

function sendSuggestion(text) {
  inputMessage.value = text
  handleSend()
}

function copyMessage(content) {
  navigator.clipboard.writeText(content)
    .then(() => ElMessage.success('已复制到剪贴板'))
    .catch(() => ElMessage.error('复制失败，请手动复制'))
}

function regenerateMessage(msg) {
  if (msg.role !== 'assistant') return
  const userMsg = messages.value.slice().reverse().find(m => m.role === 'user' && m.id < msg.id)
  if (!userMsg) {
    ElMessage.warning('找不到对应的用户消息')
    return
  }
  const msgIndex = messages.value.findIndex(m => m.id === msg.id)
  if (msgIndex > -1) messages.value.splice(msgIndex, 1)
  sendMessage(userMsg.content)
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

function scrollToBottom(force = false) {
  nextTick(() => {
    if (!messagesScroll.value) return
    if (force || !userScrolled.value) {
      messagesScroll.value.scrollTop = messagesScroll.value.scrollHeight
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
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: transparent;
}

.messages-section {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.hero-welcome {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 40px 20px;
}

.welcome-stage {
  text-align: center;
  max-width: 900px;
  width: 100%;
  animation: heroFadeIn 0.8s ease;
}

@keyframes heroFadeIn {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.hero-logo {
  position: relative;
  display: inline-block;
  margin-bottom: 48px;
}

.logo-orb {
  position: absolute;
  border-radius: 50%;
  animation: orbit 6s ease-in-out infinite;
}

.orb-1 {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(99, 102, 241, 0.1) 100%);
  top: -30px;
  left: -40px;
  animation-delay: 0s;
}

.orb-2 {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.3) 0%, rgba(14, 165, 233, 0.1) 100%);
  top: -20px;
  right: -30px;
  animation-delay: -2s;
}

.orb-3 {
  width: 90px;
  height: 90px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.3) 0%, rgba(245, 158, 11, 0.1) 100%);
  bottom: -25px;
  left: -20px;
  animation-delay: -4s;
}

@keyframes orbit {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(15px, -15px) scale(1.1); }
  66% { transform: translate(-10px, 10px) scale(0.95); }
}

.logo-center {
  width: 130px;
  height: 130px;
  border-radius: 40px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  position: relative;
  z-index: 2;
  overflow: hidden;
  animation: logoFloat 3s ease-in-out infinite;
}

@keyframes logoFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 40px;
}

.hero-text {
  margin-bottom: 56px;
}

.hero-title {
  font-size: 52px;
  font-weight: 800;
  letter-spacing: -1.5px;
  color: #0f172a;
  margin-bottom: 16px;
  line-height: 1.1;
}

.gradient-text {
  background: linear-gradient(135deg, #6366f1 0%, #0ea5e9 50%, #f59e0b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  background-size: 200% 200%;
  animation: gradientMove 4s ease infinite;
}

@keyframes gradientMove {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.hero-subtitle {
  font-size: 20px;
  color: #475569;
  line-height: 1.6;
  max-width: 600px;
  margin: 0 auto;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 56px;
}

.feature-card {
  padding: 28px 24px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  text-align: left;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  animation: cardIn 0.6s ease both;
  position: relative;
  overflow: hidden;
}

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #6366f1, #0ea5e9, #f59e0b);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15);
  border-color: rgba(99, 102, 241, 0.3);
}

.feature-card:hover::before {
  opacity: 1;
}

.feature-icon {
  font-size: 36px;
  margin-bottom: 16px;
}

.feature-content h3 {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
}

.feature-content p {
  font-size: 14px;
  color: #64748b;
  line-height: 1.5;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  max-width: 700px;
  margin: 0 auto;
}

.action-button {
  padding: 20px 28px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(14, 165, 233, 0.05) 100%);
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  overflow: hidden;
  animation: buttonIn 0.5s ease both;
}

@keyframes buttonIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.button-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.action-button:hover {
  background: white;
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateY(-4px);
  box-shadow: 0 20px 40px -12px rgba(99, 102, 241, 0.25);
}

.action-button:hover .button-glow {
  opacity: 1;
}

.button-text {
  font-size: 16px;
  font-weight: 600;
  color: #475569;
  position: relative;
  z-index: 1;
  transition: color 0.3s ease;
}

.action-button:hover .button-text {
  color: #6366f1;
}

.button-arrow {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6366f1;
  position: relative;
  z-index: 1;
  transition: all 0.3s ease;
}

.action-button:hover .button-arrow {
  transform: translateX(4px) scale(1.1);
  box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px 0;
}

.message-card {
  display: flex;
  gap: 20px;
  animation: messageSlide 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) both;
}

@keyframes messageSlide {
  from {
    opacity: 0;
    transform: translateY(40px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.message-avatar {
  flex-shrink: 0;
  padding-top: 8px;
}

.avatar-circle {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 22px;
  overflow: hidden;
}

.avatar-circle.user {
  background: transparent;
  color: #6366f1;
}

.avatar-circle.assistant {
  background: white;
  border: 2px solid #e2e8f0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 16px;
}

.message-bubble {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.sender-name {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.message-time {
  font-size: 13px;
  color: #94a3b8;
}

.thinking-box {
  margin-bottom: 16px;
}

.thinking-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(14, 165, 233, 0.05) 100%);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 14px;
  cursor: pointer;
  color: #6366f1;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.thinking-toggle:hover {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(14, 165, 233, 0.08) 100%);
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.15);
}

.thinking-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.thinking-emoji {
  font-size: 16px;
  margin-left: auto;
}

.thinking-content {
  padding: 18px;
  background: rgba(248, 250, 252, 0.8);
  border: 1px solid #e2e8f0;
  border-radius: 0 0 14px 14px;
  margin-top: -6px;
  border-top: none;
}

.thinking-content p {
  font-size: 14px;
  line-height: 1.7;
  color: #475569;
  white-space: pre-wrap;
}

.message-content {
  position: relative;
}

.message-text {
  font-size: 16px;
  line-height: 1.8;
  color: #1e293b;
  word-wrap: break-word;
}

.message-text :deep(p) {
  margin: 0 0 16px;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(code) {
  background: rgba(99, 102, 241, 0.1);
  padding: 3px 10px;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
  color: #6366f1;
}

.message-text :deep(pre) {
  background: #0f172a;
  padding: 20px;
  border-radius: 16px;
  overflow-x: auto;
  margin: 18px 0;
  border: 1px solid #334155;
}

.message-text :deep(pre code) {
  background: none;
  color: #e2e8f0;
  padding: 0;
}

.typing-dots {
  display: flex;
  gap: 8px;
  padding: 12px 0;
}

.typing-dots span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #0ea5e9);
  animation: bounce 1.4s infinite ease-in-out both;
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}

.typing-dots span:nth-child(1) { animation-delay: -0.32s; }
.typing-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

.message-actions {
  display: flex;
  gap: 12px;
  margin-top: 14px;
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.3s ease;
}

.message-card:hover .message-actions {
  opacity: 1;
  transform: translateY(0);
}

.action-link {
  padding: 8px 16px;
  border: none;
  background: rgba(248, 250, 252, 0.8);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.action-link:hover {
  background: white;
  border-color: rgba(99, 102, 241, 0.3);
  color: #6366f1;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.1);
}

.input-area {
  padding: 24px 0 32px;
  border-top: 1px solid #e2e8f0;
  background: linear-gradient(0deg, rgba(248, 250, 252, 0.9) 0%, transparent 100%);
}

.input-wrapper {
  max-width: 900px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: 16px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 16px 20px;
  transition: all 0.4s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.input-wrapper:focus-within {
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1), 0 10px 40px rgba(99, 102, 241, 0.15);
  transform: translateY(-2px);
}

.input-field {
  flex: 1;
}

.chat-textarea {
  width: 100%;
  border: none;
  background: transparent;
  color: #0f172a;
  font-size: 16px;
  line-height: 1.6;
  resize: none;
  outline: none;
  font-family: inherit;
  max-height: 200px;
}

.chat-textarea::placeholder {
  color: #94a3b8;
}

.send-btn {
  width: 52px;
  height: 52px;
  border: 2px solid #6366f1;
  border-radius: 16px;
  background: transparent;
  color: #6366f1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.1) rotate(5deg);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.45);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.send-inner {
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.input-tip {
  text-align: center;
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.tip-icon {
  font-size: 16px;
}

.input-tip span {
  font-size: 13px;
  color: #94a3b8;
}

@media (max-width: 1200px) {
  .feature-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 38px;
  }
  
  .hero-subtitle {
    font-size: 16px;
  }
  
  .feature-cards {
    grid-template-columns: 1fr;
  }
  
  .quick-actions {
    grid-template-columns: 1fr;
  }
  
  .messages-list {
    gap: 20px;
  }
  
  .message-actions {
    opacity: 1;
    transform: translateY(0);
  }
  
  .action-link span {
    display: none;
  }
  
  .action-link {
    padding: 10px;
  }
}
</style>
