import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatView.vue')
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue')
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: () => import('@/views/KnowledgeGraphView.vue')
  },
  {
    path: '/features',
    name: 'Features',
    component: () => import('@/views/FeaturesView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
