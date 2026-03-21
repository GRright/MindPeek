import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useProfileStore = defineStore('profile', () => {
  const currentUserId = ref('demo_user')
  const profile = ref(null)
  const features = ref([])
  const conversations = ref([])
  const knowledgeGraph = ref(null)
  const loading = ref(false)
  const error = ref(null)

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
