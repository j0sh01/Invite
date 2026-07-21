import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

import {
  FrappeUI,
  Button,
  Input,
  TextInput,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  setConfig,
  frappeRequest,
  FeatherIcon,
} from 'frappe-ui'

let globalComponents = {
  Button,
  TextInput,
  Input,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  FeatherIcon,
}

// create a pinia instance
let pinia = createPinia()

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)
app.use(router)

for (let key in globalComponents) {
  app.component(key, globalComponents[key])
}

// Register __() translation helper globally
function __(text) {
  return text
}
window.__ = __
app.config.globalProperties.__ = __

let socket
if (import.meta.env.DEV) {
  frappeRequest({ url: '/api/method/invite.www.invite.get_context_for_dev' }).then(
    (values) => {
      for (let key in values) {
        window[key] = values[key]
      }
      app.mount('#app')
    },
  )
} else {
  app.mount('#app')
}
