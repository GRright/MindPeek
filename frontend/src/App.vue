<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <aside class="sidebar">
        <div class="sidebar-header">
          <div class="logo">
            <el-icon :size="24"><Cpu /></el-icon>
            <span class="logo-text">MindPeek</span>
          </div>
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
            <span class="nav-text">{{ item.label }}</span>
          </router-link>
        </nav>

        <div class="sidebar-footer">
          <div class="user-section">
            <el-icon :size="18"><Setting /></el-icon>
            <span class="nav-text">设置</span>
          </div>
        </div>
      </aside>

      <main class="main-content">
        <header class="top-bar">
          <div class="page-title">{{ currentPageTitle }}</div>
          <div class="top-bar-actions">
            <el-button
              type="primary"
              class="config-btn"
              @click="showConfigDialog = true"
            >
              <el-icon><Setting /></el-icon>
              <span>API 配置</span>
            </el-button>
          </div>
        </header>

        <div class="content-area">
          <router-view />
        </div>
      </main>

      <el-dialog v-model="showConfigDialog" title="API 配置" width="500px" class="config-dialog">
        <api-config @configured="showConfigDialog = false" />
      </el-dialog>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import ApiConfig from './components/ApiConfig.vue'
import {
  Cpu,
  ChatDotRound,
  UserFilled,
  Connection,
  List,
  Setting
} from '@element-plus/icons-vue'

const route = useRoute()
const showConfigDialog = ref(false)

const navItems = [
  { path: '/chat', label: '对话分析', icon: 'ChatDotRound' },
  { path: '/profile', label: '用户画像', icon: 'UserFilled' },
  { path: '/knowledge-graph', label: '知识图谱', icon: 'Connection' },
  { path: '/features', label: '特征管理', icon: 'List' }
]

const routeNameMap = {
  '/chat': '对话分析',
  '/profile': '用户画像',
  '/knowledge-graph': '知识图谱',
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
  --bg-primary: #0f1117;
  --bg-secondary: #1a1b26;
  --bg-tertiary: #24253a;
  --bg-hover: #2a2b3d;
  --border-color: #2e2f42;
  --text-primary: #f0f0f2;
  --text-secondary: #a0a1ad;
  --text-muted: #6b6c7d;
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
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
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
}

.nav-item.active {
  background: var(--accent-color);
  color: white;
}

.nav-item .el-icon {
  flex-shrink: 0;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
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

.top-bar-actions {
  display: flex;
  gap: 12px;
}

.config-btn {
  background: var(--bg-tertiary) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-primary) !important;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  height: 36px;
  font-weight: 500;
}

.config-btn:hover {
  background: var(--bg-hover) !important;
  border-color: var(--accent-color) !important;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--bg-primary);
}

.config-dialog .el-dialog {
  background: var(--bg-secondary) !important;
  border: 1px solid var(--border-color);
}

.config-dialog .el-dialog__header {
  border-bottom: 1px solid var(--border-color);
}

.config-dialog .el-dialog__title {
  color: var(--text-primary);
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
</style>