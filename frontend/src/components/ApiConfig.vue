<template>
  <el-form label-width="100px">
    <el-form-item label="选择模型">
      <el-select v-model="selectedProvider" placeholder="请选择LLM提供者" style="width: 100%">
        <el-option
          v-for="provider in providers"
          :key="provider.provider"
          :label="provider.provider"
          :value="provider.provider"
        >
          <span>{{ provider.provider }}</span>
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
      <el-button type="primary" @click="saveConfig" :loading="saving">
        保存配置
      </el-button>
    </el-form-item>
  </el-form>
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
