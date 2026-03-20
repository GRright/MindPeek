import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default {
  async chat(userId, message, sessionId = null) {
    return api.post('/chat', {
      user_id: userId,
      message,
      session_id: sessionId,
      extract_features: true
    })
  },

  async getProfile(userId) {
    return api.get(`/profile/${userId}`)
  },

  async getProfileSummary(userId) {
    return api.get(`/profile/${userId}/summary`)
  },

  async getFeatures(userId, featureType = null) {
    const params = featureType ? { feature_type: featureType } : {}
    return api.get(`/profile/${userId}/features`, { params })
  },

  async addFeature(userId, feature) {
    return api.post(`/profile/${userId}/features`, feature)
  },

  async getConversations(userId, limit = 50) {
    return api.get(`/profile/${userId}/conversations`, { params: { limit } })
  },

  async getKnowledgeGraph(userId = null) {
    if (userId) {
      return api.get(`/knowledge-graph/${userId}`)
    }
    return api.get('/knowledge-graph')
  },

  async getLLMProviders() {
    return api.get('/llm/providers')
  },

  async updateLLMConfig(provider, apiKey, model = null, apiUrl = null) {
    return api.post('/llm/config', {
      provider,
      api_key: apiKey,
      model,
      api_url: apiUrl
    })
  },

  async healthCheck() {
    return api.get('/health')
  }
}
