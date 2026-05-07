import { createApp } from "vue";
import App from "./App.vue";
import "./assets/styles/index.css";
import router from "./router";
import { VueTelegramPlugin } from "vue-tg";
import { createPinia } from "pinia";
import VCalendar from "v-calendar";
import "v-calendar/style.css";

const app = createApp(App);
const pinia = createPinia();

app.use(router);
app.use(pinia);
app.use(VueTelegramPlugin);
app.use(VCalendar);

const BASE_SITE = import.meta.env.VITE_API_BASE_URL || "";

const getTelegramUserId = (): string | null => {
  const tgUser = window.Telegram?.WebApp?.initDataUnsafe?.user;

  if (tgUser?.id) {
    return String(tgUser.id);
  }

  const urlParams = new URLSearchParams(window.location.search);
  const tgUserIdFromUrl = urlParams.get("tg_user_id");

  if (tgUserIdFromUrl) {
    return tgUserIdFromUrl;
  }

  return null;
};

const TG_USER_ID = getTelegramUserId();

console.log("Using TG_USER_ID:", TG_USER_ID);

app.provide("BASE_SITE", BASE_SITE);
app.provide("TG_USER_ID", TG_USER_ID);

app.mount("#app");