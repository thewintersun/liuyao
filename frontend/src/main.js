import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/styles/theme.css'
import { initLocale, t } from './utils/locale.js'

async function bootstrap() {
  await initLocale()
  const app = createApp(App)
  app.config.globalProperties.$t = t
  app.use(router)
  app.mount('#app')
}

bootstrap()
