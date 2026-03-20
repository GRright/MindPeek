<template>
  <div class="api-config">
    <el-form label-width="100px" class="config-form">
      <el-form-item label="选择模型">
        <el-select v-model="selectedProvider" placeholder="请选择LLM提供者" style="width: 100%">
          <el-option
            v-for="provider in providers"
            :key="provider.provider"
            :label="provider.provider"
            :value="provider.provider"
          >
            <span class="provider-label">{{ provider.provider }}</span>
            <el-tag v-if="provider.configured" type="success" size="small" style="margin-left: 10px">
              已配置
            </el-tag>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="API Key">
        <el-input
          v-model="apiKey"
          type="password"
          show-password
          placeholder="请输入API Key"
        />
      </el-form-item>

      <el-form-item label="模型名称">
        <el-input
          v-model="model"
          placeholder="可选，使用默认模型"
        />
      </el-form-item>

      <el-form-item label="API地址">
        <el-input
          v-model="apiUrl"
          placeholder="可选，使用默认地址"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="saveConfig" :loading="saving" class="save-btn">
          保存配置
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const emit = defineEmits(['configured'])

const providers = ref([])
const selectedProvider = ref('qwen')
const apiKey = ref('')
const model = ref('')
const apiUrl = ref('')
const saving = ref(false)

onMounted(async () => {
  try {
    providers.value = await api.getLLMProviders()
  } catch (e) {
    console.error('Failed to load providers:', e)
  }
})

async function saveConfig() {
  if (!apiKey.value && selectedProvider.value !== 'ollama') {
    ElMessage.warning('请输入API Key')
    return
  }

  saving.value = true
  try {
    await api.updateLLMConfig(
      selectedProvider.value,
      apiKey.value,
      model.value || null,
      apiUrl.value || null
    )
    ElMessage.success('配置保存成功')
    emit('configured')
  } catch (e) {
    ElMessage.error('配置保存失败: ' + e.message)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.api-config {
  padding: 8px 0;
}

.config-form :deep(.el-form-item__label) {
  color: var(--text-secondary);
}

.config-form :deep(.el-input__wrapper) {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  box-shadow: none;
}

.config-form :deep(.el-input__inner) {
  color: var(--text-primary);
}

.config-form :deep(.el-input__inner::placeholder) {
  color: var(--text-muted);
}

.provider-label {
  color: var(--text-primary);
}

.save-btn {
  width: 100%;
  background: var(--accent-color) !important;
  border: none !important;
  height: 40px;
  font-weight: 500;
}

.save-btn:hover {
  background: var(--accent-hover) !important;
}
</style>