<template>
  <section class="py-8">
    <div class="max-w-6xl mx-auto px-4">
      <div v-if="authStore.isLoading" class="text-center text-gray-500">
        Проверяем доступ...
      </div>

      <div
          v-else-if="!authStore.isAdmin"
          class="rounded-3xl bg-red-50 border border-red-100 p-6 text-center text-red-700"
      >
        {{ authStore.errorMessage }}
      </div>

      <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <div
            v-for="group in groups"
            :key="group.title"
            class="rounded-3xl bg-purple-50 border border-purple-100 p-6 shadow-sm"
        >
          <h2 class="text-xl text-center font-bold text-purple-900 mb-4">
            {{ group.title }}
          </h2>

          <div class="space-y-3">
            <button
                v-for="item in group.items"
                :key="item.title"
                type="button"
                class="w-full rounded-2xl bg-white px-4 py-3 text-left font-medium text-gray-900 border border-purple-100 hover:bg-purple-100 hover:text-purple-900 transition"
                @click="$router.push(item.route)"
            >
              {{ item.title }}
            </button>
          </div>
        </div>
      </div>
    </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useAuthStore } from "../stores/authStore";

const authStore = useAuthStore();

onMounted(async () => {
  window.Telegram?.WebApp?.ready();
  window.Telegram?.WebApp?.expand();

  await authStore.checkAdmin();
});

const groups = [
  {
    title: 'Расписание',
    items: [
      { title: 'Сгенерировать рабочее время мастера', route: '/admin/schedule/generate' },
    ],
  },
    {
    title: 'Клиенты и записи',
    items: [
      { title: 'Добавить клиента', route: '/admin/clients/create' },
      { title: 'Записать клиента вручную', route: '/admin/bookings/create' },
    ],
  },
    {
    title: 'Услуги',
    items: [
      { title: 'Получить список услуг', route: '/admin/services' },
      { title: 'Добавить услугу', route: '/admin/services/create' },
      { title: 'Обновить услугу', route: '/admin/services/update' },
    ],
  },
  {
    title: 'Мастера',
    items: [
      { title: 'Добавить мастера', route: '/admin/specialists/create' },
      { title: 'Изменить данные мастера', route: '/admin/specialists/update' },
      { title: 'Привязать услугу к мастеру', route: '/admin/specialist-services/create' },
    ],
  },
];
</script>