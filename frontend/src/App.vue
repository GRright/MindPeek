<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <div class="logo" v-show="!sidebarCollapsed">
            <el-icon :size="24"><Cpu /></el-icon>
            <span class="logo-text">MindPeek</span>
          </div>
          <el-button
            class="collapse-btn"
            @click="sidebarCollapsed = !sidebarCollapsed"
            :icon="sidebarCollapsed ? 'DArrowRight' : 'DArrowLeft'"
            circle
            plain
          />
        </div>

        <nav class="sidebar-nav">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: isActive(item.path) }"
          >
            <el-icon :size="20"><component :is="item.icon" /></el-icon>
            <span class="nav-text" v-show="!sidebarCollapsed">{{ item.label }}</span>
          </router-link>
        </nav>

        <div class="sidebar-footer"></div>
      </aside>

      <main class="main-content">
        <header class="top-bar">
          <div class="page-title">{{ currentPageTitle }}</div>
        </header>

        <div class="content-area">
          <router-view v-slot="{ Component }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>

    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import {
  Cpu,
  ChatDotRound,
  UserFilled,
  Connection,
  List,
  DArrowLeft,
  DArrowRight
} from '@element-plus/icons-vue'

const route = useRoute()
const sidebarCollapsed = ref(false)

const BREAKPOINT = 1024

const handleResize = () => {
  if (window.innerWidth <= BREAKPOINT) {
    sidebarCollapsed.value = true
  } else {
    sidebarCollapsed.value = false
  }
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const navItems = [
  { path: '/chat', label: '对话分析', icon: 'ChatDotRound' },
  { path: '/profile', label: '用户画像', icon: 'UserFilled' },
  { path: '/knowledge-graph', label: '特征图谱', icon: 'Connection' },
  { path: '/features', label: '特征管理', icon: 'List' }
]

const routeNameMap = {
  '/chat': '对话分析',
  '/profile': '用户画像',
  '/knowledge-graph': '特征图谱',
  '/features': '特征管理'
}

const currentPageTitle = computed(() => routeNameMap[route.path] || 'MindPeek')

function isActive(path) {
  return route.path === path
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

:root {
  --bg-primary: #ffffff;
  --bg-secondary: #f5f6fa;
  --bg-tertiary: #e8eaed;
  --bg-hover: #e2e5ea;
  --border-color: #dde1e7;
  --text-primary: #1a1b26;
  --text-secondary: #5c5f6a;
  --text-muted: #8b8d96;
  --accent-color: #6366f1;
  --accent-hover: #818cf8;
  --danger-color: #ef4444;
  --success-color: #22c55e;
  --warning-color: #f59e0b;
}

.app-container {
  display: flex;
  height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.sidebar {
  width: 240px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.collapse-btn {
  flex-shrink: 0;
  margin-left: auto;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 20px 12px;
}

.sidebar.collapsed .collapse-btn {
  margin-left: 0;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 12px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-primary);
}

.logo .el-icon {
  color: var(--accent-color);
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  transform: translateX(4px);
}

.nav-item.active {
  background: var(--accent-color);
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.nav-item .el-icon {
  flex-shrink: 0;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.2s ease, width 0.3s ease;
}

.sidebar.collapsed .nav-text {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.sidebar-footer {
  padding: 16px 12px;
  border-top: 1px solid var(--border-color);
}

.user-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.user-section:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-bar {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg-primary);
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-primary);
}

::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--bg-hover);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

@media (max-width: 1024px) {
  .top-bar {
    padding: 0 16px;
  }

  .content-area {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .top-bar .page-title {
    font-size: 16px;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-animate {
  animation: fadeInUp 0.4s ease-out forwards;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.pulse-hover:hover {
  animation: pulse 0.3s ease-in-out;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.loading-shimmer {
  background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-hover) 50%, var(--bg-tertiary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
</style>