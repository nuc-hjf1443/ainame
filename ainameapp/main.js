import App from './App'

const installDynamicImportRecovery = app => {
  if (typeof window === 'undefined') return;
  const marker = 'ainame_dynamic_import_recovered';
  const shouldRecover = error => {
    const message = String(error?.message || error?.reason?.message || error?.reason || error || '');
    return message.includes('Failed to fetch dynamically imported module') || message.includes('Importing a module script failed');
  };
  const recover = error => {
    if (!shouldRecover(error)) return;
    if (sessionStorage.getItem(marker)) return;
    sessionStorage.setItem(marker, '1');
    setTimeout(() => window.location.reload(), 300);
  };
  window.addEventListener('error', event => recover(event.error || event.message));
  window.addEventListener('unhandledrejection', event => recover(event.reason));
  if (app?.config) {
    const previousHandler = app.config.errorHandler;
    app.config.errorHandler = (error, instance, info) => {
      recover(error);
      if (previousHandler) previousHandler(error, instance, info);
      else console.error(error);
    };
  }
  window.addEventListener('load', () => {
    setTimeout(() => sessionStorage.removeItem(marker), 5000);
  });
};

// #ifndef VUE3
import Vue from 'vue'
import './uni.promisify.adaptor'
Vue.config.productionTip = false
App.mpType = 'app'
installDynamicImportRecovery(Vue)
const app = new Vue({
  ...App
})
app.$mount()
// #endif

// #ifdef VUE3
import { createSSRApp } from 'vue'
export function createApp() {
  const app = createSSRApp(App)
  installDynamicImportRecovery(app)
  return {
    app
  }
}
// #endif
