import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import api from '@/api'

const STORAGE_KEY = 'mindpeek_user_id'
const MULTIMODAL_KEY = 'mindpeek_multimodal'

function getInitialUserId() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) return stored
  localStorage.setItem(STORAGE_KEY, 'MindPeek')
  return 'MindPeek'
}

function getInitialMultimodal() {
  const stored = localStorage.getItem(MULTIMODAL_KEY)
  return stored === 'true'
}

export const useProfileStore = defineStore('profile', () => {
  const currentUserId = ref(getInitialUserId())
  const profile = ref(null)
  const features = ref([])
  const conversations = ref([])
  const knowledgeGraph = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const multimodalEnabled = ref(getInitialMultimodal())

  watch(currentUserId, (newId) => {
    localStorage.setItem(STORAGE_KEY, newId)
  })

  function setMultimodalEnabled(enabled) {
    multimodalEnabled.value = enabled
    localStorage.setItem(MULTIMODAL_KEY, String(enabled))
  }

  const mbti = computed(() => {
    if (!features.value) return null
    const mbtiFeature = features.value.find(f => f.feature_type === 'MBTI')
    return mbtiFeature ? mbtiFeature.feature_value : null
  })

  const behaviorHabits = computed(() => {
    if (!features.value) return []
    return features.value
      .filter(f => f.feature_type === '行为习惯')
      .map(f => ({
        value: f.feature_value,
        confidence: f.confidence
      }))
  })

  const potentialThoughts = computed(() => {
    if (!features.value) return []
    return features.value
      .filter(f => f.feature_type === '潜在想法')
      .map(f => ({
        value: f.feature_value,
        confidence: f.confidence
      }))
  })

  async function sendMessage(message, deepThink = false) {
    loading.value = true
    error.value = null
    try {
      const result = await api.chat(currentUserId.value, message, null, deepThink)

      await loadProfile()
      await loadConversations()

      return result
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadProfile() {
    try {
      const data = await api.getProfile(currentUserId.value)
      profile.value = data.profile
      features.value = data.features || []
      return data
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function loadConversations(limit = 50) {
    try {
      const data = await api.getConversations(currentUserId.value, limit)
      conversations.value = data
      return data
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function loadKnowledgeGraph() {
    try {
      const data = await api.getKnowledgeGraph(currentUserId.value)
      knowledgeGraph.value = data
      return data
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function addFeature(feature) {
    try {
      const result = await api.addFeature(currentUserId.value, feature)
      await loadProfile()
      return result
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  function setUserId(userId) {
    currentUserId.value = userId
  }

  return {
    currentUserId,
    profile,
    features,
    conversations,
    knowledgeGraph,
    loading,
    error,
    mbti,
    behaviorHabits,
    potentialThoughts,
    sendMessage,
    loadProfile,
    loadConversations,
    loadKnowledgeGraph,
    addFeature,
    setUserId
  }
})
