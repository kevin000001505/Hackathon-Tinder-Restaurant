import './assets/main.css'

import { createApp } from 'vue'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice';
import ToastService from 'primevue/toastservice';
import Aura from '@primevue/themes/aura'
import App from './App.vue'

const app = createApp(App)
app.use(ConfirmationService);
app.use(ToastService);
app.use(PrimeVue, {
    theme: {
        preset: Aura,
    },
})
app.mount('#app')
