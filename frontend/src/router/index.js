import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { tab: 'qigua' } },
  { path: '/yao-input', name: 'YaoInput', component: () => import('../views/YaoInput.vue'), meta: { tab: 'qigua' } },
  { path: '/hexagram', name: 'Hexagram', component: () => import('../views/Hexagram.vue'), meta: { tab: 'qigua' } },
  { path: '/category', name: 'Category', component: () => import('../views/Category.vue'), meta: { tab: 'qigua' } },
  { path: '/analysis', name: 'Analysis', component: () => import('../views/Analysis.vue'), meta: { tab: 'qigua' } },
  { path: '/chat', name: 'Chat', component: () => import('../views/Chat.vue'), meta: { tab: 'qigua' } },
  { path: '/records', name: 'Records', component: () => import('../views/Records.vue'), meta: { tab: 'records' } },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue'), meta: { tab: 'settings' } },
  { path: '/guide', name: 'Guide', component: () => import('../views/Guide.vue'), meta: { tab: 'settings' } },
  { path: '/disclaimer', name: 'Disclaimer', component: () => import('../views/Disclaimer.vue'), meta: { tab: 'settings' } },
  { path: '/terms-privacy', name: 'TermsPrivacy', component: () => import('../views/Terms.vue'), meta: { tab: 'settings' } },
  { path: '/feedback', name: 'Feedback', component: () => import('../views/Feedback.vue'), meta: { tab: 'settings' } },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { tab: 'qigua' } },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('../views/ForgotPassword.vue'), meta: { tab: 'qigua' } },
  { path: '/reset-password', name: 'ResetPassword', component: () => import('../views/ResetPassword.vue'), meta: { tab: 'qigua' } },
  { path: '/account', name: 'Account', component: () => import('../views/Account.vue'), meta: { tab: 'settings' } },
  { path: '/invite', name: 'Invite', component: () => import('../views/Invite.vue'), meta: { tab: 'settings' } },
  // 管理后台路由
  { path: '/admin', name: 'AdminDashboard', component: () => import('../views/admin/Dashboard.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/users', name: 'AdminUsers', component: () => import('../views/admin/Users.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/users/:id', name: 'AdminUserDetail', component: () => import('../views/admin/UserDetail.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/config', name: 'AdminConfig', component: () => import('../views/admin/SystemConfig.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/prompts', name: 'AdminPrompts', component: () => import('../views/admin/Prompts.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/feedback', name: 'AdminFeedback', component: () => import('../views/admin/Feedback.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/logs', name: 'AdminLogs', component: () => import('../views/admin/Logs.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/logs/session/:sessionId', name: 'AdminLogDetail', component: () => import('../views/admin/LogDetail.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 管理页面路由守卫
router.beforeEach((to, from, next) => {
  if (to.meta.requireAdmin) {
    const user = JSON.parse(localStorage.getItem('liuyao_user') || '{}')
    if (user.role !== 'admin') {
      next('/settings')
      return
    }
  }
  next()
})

export default router
