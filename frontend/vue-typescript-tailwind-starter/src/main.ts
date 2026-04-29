import { createApp } from "vue";
import App from "./App.vue";
import "./assets/styles/index.css";
import router from "./router";
import { VueTelegramPlugin } from "vue-tg";

const app = createApp(App);
app.use(router);
app.use(VueTelegramPlugin);

// Получаем параметры из URL
const urlParams = new URLSearchParams(window.location.search);
const tgUserIdFromUrl = urlParams.get('tg_user_id');

// Для разработки используем localhost с прокси, для продакшена - реальный URL
const isDevelopment = import.meta.env.MODE === 'development';
const BASE_SITE = isDevelopment ? '' : 'https://fd6ae8ea313e.ngrok-free.app';

// Сохраняем TG_USER_ID в localStorage для использования на всех страницах
if (tgUserIdFromUrl) {
    localStorage.setItem('tg_user_id', tgUserIdFromUrl);
    console.log('TG_USER_ID saved to localStorage:', tgUserIdFromUrl);
}

// Используем TG_USER_ID из URL, localStorage или fallback для разработки
const TG_USER_ID = tgUserIdFromUrl || localStorage.getItem('tg_user_id') || (isDevelopment ? '584149528' : null);

console.log('Using TG_USER_ID:', TG_USER_ID);

app.provide("BASE_SITE", BASE_SITE);
app.provide("TG_USER_ID", TG_USER_ID);
app.mount("#app");