<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <div class="hero-gradient"></div>
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
      </div>
      
      <div class="top-navigation">
        <div class="nav-container">
          <div class="logo-section" @click="$router.push('/chat')">
            <div class="logo-icon">
              <img :src="logo" alt="MindPeek" class="logo-img" />
            </div>
            <span class="logo-text">MindPeek</span>
          </div>
          
          <nav class="nav-links">
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              class="nav-link"
              :class="{ active: isActive(item.path) }"
            >
              <div class="nav-indicator"></div>
              <el-icon :size="20"><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </router-link>
          </nav>
          
          <div class="nav-right">
            <div class="version-badge">
              <span>v3.0</span>
            </div>
          </div>
        </div>
      </div>

      <main class="main-content">
        <div class="page-header">
          <div class="header-content">
            <div class="title-badge">
              <el-icon :size="18"><Star /></el-icon>
              <span>{{ currentPageTitle }}</span>
            </div>
            <h1 class="page-title">{{ currentPageTitle }}</h1>
            <p class="page-subtitle">{{ currentPageSubtitle }}</p>
          </div>
        </div>

        <div class="content-wrapper">
          <router-view v-slot="{ Component, route }">
            <transition :name="getTransitionName(route)" mode="out-in" appear>
              <component :is="Component" :key="route.path" />
            </transition>
          </router-view>
        </div>
      </main>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import logo from './assets/logo.png'
import {
  ChatDotRound,
  User,
  Connection,
  Document,
  Star
} from '@element-plus/icons-vue'

const route = useRoute()

const navItems = [
  { path: '/chat', label: '智能对话', icon: 'ChatDotRound', subtitle: '通过对话了解你' },
  { path: '/profile', label: '用户画像', icon: 'User', subtitle: '深入的个性分析' },
  { path: '/knowledge-graph', label: '特征图谱', icon: 'Connection', subtitle: '可视化关系网络' },
  { path: '/features', label: '特征管理', icon: 'Document', subtitle: '查看和管理特征' }
]

const routeNameMap = {
  '/chat': { title: '智能对话', subtitle: '通过持续对话，让AI真正理解你' },
  '/profile': { title: '用户画像', subtitle: '基于大语言模型的深度个性分析' },
  '/knowledge-graph': { title: '特征图谱', subtitle: '可视化展示特征之间的关联网络' },
  '/features': { title: '特征管理', subtitle: '查看、编辑和管理所有提取的特征' }
}

const currentPageTitle = computed(() => routeNameMap[route.path]?.title || 'MindPeek')
const currentPageSubtitle = computed(() => routeNameMap[route.path]?.subtitle || '')

function isActive(path) {
  return route.path === path
}

const routeOrder = ['/chat', '/profile', '/knowledge-graph', '/features']
let lastRouteIndex = 0

function getTransitionName(route) {
  const currentIndex = routeOrder.indexOf(route.path)
  let transitionName = 'hero-fade'
  
  if (currentIndex > lastRouteIndex) {
    transitionName = 'hero-up'
  } else if (currentIndex < lastRouteIndex) {
    transitionName = 'hero-down'
  }
  
  lastRouteIndex = currentIndex
  return transitionName
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+SC:wght@300;400;500;600;700;800&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  overflow: hidden;
}

:root {
  --color-primary: #6366f1;
  --color-primary-dark: #4f46e5;
  --color-primary-light: #818cf8;
  --color-secondary: #0ea5e9;
  --color-accent: #f59e0b;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  --bg-hover: #e2e8f0;
  
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  
  --border-light: #e2e8f0;
  --border-medium: #cbd5e1;
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --radius-xl: 28px;
  --radius-2xl: 36px;
  
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 300ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 500ms cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 50%, #f8fafc 100%);
  color: var(--text-primary);
  overflow: hidden;
  position: relative;
}

.hero-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 500px;
  background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.15) 0%, rgba(14, 165, 233, 0.1) 30%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}

.floating-shapes {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.6;
  animation: float 20s ease-in-out infinite;
}

.shape-1 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%);
  top: 10%;
  left: 5%;
  animation-delay: 0s;
}

.shape-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.08) 0%, rgba(14, 165, 233, 0.03) 100%);
  top: 60%;
  right: -100px;
  animation-delay: -7s;
}

.shape-3 {
  width: 250px;
  height: 250px;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.08) 0%, rgba(245, 158, 11, 0.03) 100%);
  bottom: 20%;
  left: 15%;
  animation-delay: -14s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1) rotate(0deg); }
  25% { transform: translate(40px, -40px) scale(1.1) rotate(5deg); }
  50% { transform: translate(-30px, 30px) scale(0.95) rotate(-5deg); }
  75% { transform: translate(30px, 40px) scale(1.05) rotate(3deg); }
}

.top-navigation {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-light);
  padding: 0;
}

.nav-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 40px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  transition: transform var(--transition-base);
}

.logo-section:hover {
  transform: scale(1.02);
}

.logo-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}



@keyframes shine {
  0% { transform: translateX(-100%) rotate(45deg); }
  100% { transform: translateX(100%) rotate(45deg); }
}

.logo-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  position: relative;
  z-index: 1;
}

.logo-text {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.8px;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--color-primary) 50%, var(--color-secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  background-size: 200% 200%;
  animation: gradientShift 4s ease infinite;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-secondary);
  padding: 8px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-light);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 15px;
  font-weight: 600;
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.nav-indicator {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
  border-radius: 0 0 2px 2px;
  transform: scaleX(0);
  transform-origin: center;
  transition: transform var(--transition-base);
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
  transform: translateY(-2px);
}

.nav-link:hover .nav-indicator {
  transform: scaleX(1);
}

.nav-link.active {
  color: var(--color-primary);
  background: white;
  box-shadow: var(--shadow-md);
}

.nav-link.active .nav-indicator {
  transform: scaleX(1);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.version-badge {
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 30px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-primary);
  letter-spacing: 0.5px;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.page-header {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.header-content {
  animation: fadeInDown 0.6s ease;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.title-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 30px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 16px;
}

.page-title {
  font-size: 48px;
  font-weight: 800;
  letter-spacing: -1.5px;
  color: var(--text-primary);
  line-height: 1.1;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 18px;
  font-weight: 400;
  color: var(--text-secondary);
  line-height: 1.6;
}

.content-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 0 40px 40px;
  position: relative;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  overflow-x: hidden;
}

.hero-up-enter-active,
.hero-up-leave-active,
.hero-down-enter-active,
.hero-down-leave-active,
.hero-fade-enter-active,
.hero-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.hero-up-enter-from {
  opacity: 0;
  transform: translateY(40px);
}

.hero-up-leave-to {
  opacity: 0;
  transform: translateY(-40px);
}

.hero-down-enter-from {
  opacity: 0;
  transform: translateY(-40px);
}

.hero-down-leave-to {
  opacity: 0;
  transform: translateY(40px);
}

.hero-fade-enter-from {
  opacity: 0;
}

.hero-fade-leave-to {
  opacity: 0;
}

.hero-up-enter-to,
.hero-down-enter-to,
.hero-fade-enter-to {
  opacity: 1;
  transform: translateY(0);
}

::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 5px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--color-primary), var(--color-secondary));
  border-radius: 5px;
  transition: all var(--transition-base);
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, var(--color-primary-dark), var(--color-secondary));
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.3);
}

@media (max-width: 1200px) {
  .nav-container {
    padding: 16px 32px;
  }
  
  .page-header {
    padding: 32px;
  }
  
  .page-title {
    font-size: 40px;
  }
  
  .content-wrapper {
    padding: 0 32px 32px;
  }
}

@media (max-width: 900px) {
  .nav-links {
    display: none;
  }
  
  .nav-container {
    padding: 16px 24px;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 24px;
  }
  
  .page-title {
    font-size: 32px;
  }
  
  .page-subtitle {
    font-size: 16px;
  }
  
  .content-wrapper {
    padding: 0 24px 24px;
  }
  
  .nav-container {
    padding: 14px 20px;
  }
  
  .logo-text {
    display: none;
  }
}
</style>
