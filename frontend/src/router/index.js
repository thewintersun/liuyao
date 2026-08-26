import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { tab: 'qigua', title: '六爻解卦 - AI智能排盘解卦' } },
  { path: '/yao-input', name: 'YaoInput', component: () => import('../views/YaoInput.vue'), meta: { tab: 'qigua', title: '起卦 - 六爻解卦' } },
  { path: '/hexagram', name: 'Hexagram', component: () => import('../views/Hexagram.vue'), meta: { tab: 'qigua', title: '卦象详情 - 六爻解卦' } },
  { path: '/category', name: 'Category', component: () => import('../views/Category.vue'), meta: { tab: 'qigua', title: '选择类别 - 六爻解卦' } },
  { path: '/analysis', name: 'Analysis', component: () => import('../views/Analysis.vue'), meta: { tab: 'qigua', title: 'AI解卦 - 六爻解卦' } },
  { path: '/chat', name: 'Chat', component: () => import('../views/Chat.vue'), meta: { tab: 'qigua', title: '对话解卦 - 六爻解卦' } },
  { path: '/records', name: 'Records', component: () => import('../views/Records.vue'), meta: { tab: 'records', title: '解卦记录 - 六爻解卦' } },
  { path: '/settings', name: 'Settings', component: () => import('../views/Settings.vue'), meta: { tab: 'settings', title: '设置 - 六爻解卦' } },
  { path: '/guide', name: 'Guide', component: () => import('../views/Guide.vue'), meta: { tab: 'settings', title: '使用指南 - 六爻解卦' } },
  { path: '/disclaimer', name: 'Disclaimer', component: () => import('../views/Disclaimer.vue'), meta: { tab: 'settings', title: '免责声明 - 六爻解卦' } },
  { path: '/terms-privacy', name: 'TermsPrivacy', component: () => import('../views/Terms.vue'), meta: { tab: 'settings', title: '用户协议与隐私政策 - 六爻解卦' } },
  { path: '/feedback', name: 'Feedback', component: () => import('../views/Feedback.vue'), meta: { tab: 'settings', title: '意见反馈 - 六爻解卦' } },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { tab: 'qigua', title: '登录 - 六爻解卦' } },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('../views/ForgotPassword.vue'), meta: { tab: 'qigua', title: '忘记密码 - 六爻解卦' } },
  { path: '/reset-password', name: 'ResetPassword', component: () => import('../views/ResetPassword.vue'), meta: { tab: 'qigua', title: '重置密码 - 六爻解卦' } },
  { path: '/account', name: 'Account', component: () => import('../views/Account.vue'), meta: { tab: 'settings', title: '账号管理 - 六爻解卦' } },
  { path: '/invite', name: 'Invite', component: () => import('../views/Invite.vue'), meta: { tab: 'settings', title: '邀请好友 - 六爻解卦' } },
  // 管理后台路由
  { path: '/admin', name: 'AdminDashboard', component: () => import('../views/admin/Dashboard.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/users', name: 'AdminUsers', component: () => import('../views/admin/Users.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/users/:id', name: 'AdminUserDetail', component: () => import('../views/admin/UserDetail.vue'), meta: { tab: 'settings', requireAdmin: true } },
  { path: '/admin/users/:id/logs', name: 'AdminUserLogs', component: () => import('../views/admin/UserLogs.vue'), meta: { tab: 'settings', requireAdmin: true } },
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

router.beforeEach((to, from, next) => {
  // 更新页面标题
  if (to.meta.title) {
    document.title = to.meta.title
  }
  // 管理页面路由守卫
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
