<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <el-header class="app-header">
          <div class="logo">
            <el-icon><User /></el-icon>
            <span>perMIR 用户画像系统</span>
          </div>
          <div class="header-actions">
            <el-button type="primary" @click="showConfigDialog = true">
              <el-icon><Setting /></el-icon>
              API配置
            </el-button>
          </div>
        </el-header>
        
        <el-container>
          <el-aside width="220px" class="app-aside">
            <el-menu
              :default-active="activeMenu"
              router
              class="side-menu"
            >
              <el-menu-item index="/chat">
                <el-icon><ChatDotRound /></el-icon>
                <span>对话分析</span>
              </el-menu-item>
              <el-menu-item index="/profile">
                <el-icon><UserFilled /></el-icon>
                <span>用户画像</span>
              </el-menu-item>
              <el-menu-item index="/knowledge-graph">
                <el-icon><Share /></el-icon>
                <span>知识图谱</span>
              </el-menu-item>
              <el-menu-item index="/features">
                <el-icon><List /></el-icon>
                <span>特征管理</span>
              </el-menu-item>
            </el-menu>
          </el-aside>
          
          <el-main class="app-main">
            <router-view />
          </el-main>
        </el-container>
      </el-container>
      
      <el-dialog v-model="showConfigDialog" title="API配置" width="500px">
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

const route = useRoute()
const showConfigDialog = ref(false)

const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.app-container {
  height: 100%;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: bold;
}

.logo .el-icon {
  font-size: 24px;
}

.header-actions .el-button {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.app-aside {
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.side-menu {
  border-right: none;
  height: 100%;
}

.app-main {
  background: #f0f2f5;
  padding: 20px;
  min-height: calc(100vh - 60px);
}
</style>
