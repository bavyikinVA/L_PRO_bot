<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { useFetch } from '@vueuse/core';
import { computed, inject, ref, watch } from 'vue';
import { getPhotoUrl } from "../utils/getPhotoUrl";

interface Specialist {
  id: number;
  first_name: string;
  last_name: string;
  work_experience: string;
  photo: string;
}

interface Service {
  id: number;
  label: string;
  description: string;
  price: number;
  duration_minutes: number;
}

interface DaySlot {
  day: string;
  date: string;
  slots: string[];
  total_slots: number;
}

interface SlotsResponse {
  days: DaySlot[];
  total_week_slots: number;
}

const BASE_SITE = inject('BASE_SITE') as string;
const TG_USER_ID = inject('TG_USER_ID') as string;
const route = useRoute();
const router = useRouter();
const serviceId = route.params.serviceId as string;
const specialistId = route.params.specialistId as string;

// Получаем информацию о специалисте
const { data: specialist } = useFetch<Specialist>(
    `${BASE_SITE}/api/specialists/${specialistId}`
).get().json();

// Получаем информацию об услуге
const { data: service } = useFetch<Service>(
    `${BASE_SITE}/api/services/${serviceId}`
).get().json();

// Получаем текущую дату для начальных слотов
const today = new Date();
const initialDate = today.toISOString().split('T')[0];
const currentStartDate = ref(initialDate);

// Создаем реактивный запрос для получения слотов
const { data: slotsWeekInfo, execute: fetchSlots } = useFetch<SlotsResponse>(
    computed(() => `${BASE_SITE}/api/specialists/${specialistId}/slots?start_date=${currentStartDate.value}&service_id=${serviceId}`),
    { immediate: true }
).get().json();

// Генерируем строку с текущей неделей
const generateCurrentWeek = computed(() => {
  if (slotsWeekInfo.value?.days?.length) {
    const days = slotsWeekInfo.value.days;
    const startDate = formatDate(days[0].date);
    const endDate = formatDate(days[days.length - 1].date);
    return `${startDate} - ${endDate}`;
  }
  return "Нет данных";
});

// Форматирование даты
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU');
};

// Функция навигации по неделям
const changeWeek = async (direction: number) => {
  const date = new Date(currentStartDate.value);
  date.setDate(date.getDate() + (direction * 7));

  // Предотвращаем выбор даты ранее текущей
  if (date < today) {
    currentStartDate.value = initialDate;
  } else {
    currentStartDate.value = date.toISOString().split('T')[0];
  }

  // Ждем обновления слотов
  await fetchSlots();
};

// Следим за изменениями даты и обновляем слоты
watch(currentStartDate, async () => {
  await fetchSlots();
}, { immediate: true });

// Функция для выбора времени
const selectTimeSlot = (day: DaySlot, timeSlot: string) => {
  if (!TG_USER_ID) {
    alert("Не удалось определить пользователя Telegram. Откройте запись через бота.");
    return;
  }

  router.push(
      `/booking-confirm?specialist_id=${specialistId}&service_id=${serviceId}&date=${day.date}&time=${timeSlot}&tg_user_id=${TG_USER_ID}`
  );
};
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Заголовок и кнопка назад -->
    <div class="mb-8">
      <button
          @click="router.back()"
          class="flex items-center text-brand hover:text-brand-dark mb-4"
      >
        <i class="fas fa-arrow-left mr-2"></i>
        Назад к специалистам
      </button>
      <h1 class="text-3xl mt-2 text-gray-800">Запись на услугу</h1>
    </div>

    <!-- Информация о специалисте и услуге -->
    <div class="flex flex-col sm:flex-row items-center mb-8 border-b pb-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow duration-300">
      <img
          v-if="specialist?.photo"
          :src="getPhotoUrl(specialist.photo)"
          :alt="`${specialist.first_name} ${specialist.last_name}`"
          class="ml-2 w-32 h-32 sm:w-40 sm:h-40 object-cover rounded-lg mr-4"
      />
      <div v-else class="w-32 h-32 sm:w-40 sm:h-40 bg-gray-200 rounded-lg mr-4 flex items-center justify-center">
        <i class="fas fa-user text-gray-400 text-4xl"></i>
      </div>

      <div class="text-center sm:text-left mt-4 sm:mt-0">
        <h2 class="text-2xl sm:text-3xl text-gray-800 mb-2">
          {{ specialist?.first_name }} {{ specialist?.last_name }}
        </h2>
        <p class="text-brand hover font-semibold text-lg">
          Услуга: {{ service?.label }}
        </p>
        <p class="text-brand" v-if="service">
          {{ service.duration_minutes }} мин • {{ service.price }} ₽
        </p>
      </div>
    </div>

    <!-- Навигация по неделям -->
    <div class="flex items-center justify-between mb-8 bg-white rounded-lg shadow-md p-4">
      <button
          class="w-12 h-12 flex items-center justify-center bg-brand hover text-white rounded-full hover:bg-brand-dark transition-all duration-300 shadow-lg hover:shadow-xl"
          @click="() => changeWeek(-1)"
          :disabled="currentStartDate === initialDate"
          :class="{ 'opacity-50 cursor-not-allowed': currentStartDate === initialDate }"
      >
        <i class="fas fa-chevron-left"></i>
      </button>

      <h3 class="text-xl font-semibold text-gray-800 text-center flex-grow mx-4">
        {{ generateCurrentWeek }}
      </h3>

      <button
          class="w-12 h-12 flex items-center justify-center bg-brand hover text-white rounded-full hover:bg-brand-dark transition-all duration-300 shadow-lg hover:shadow-xl"
          @click="() => changeWeek(1)"
      >
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>

    <!-- Дни недели со слотами -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" v-if="slotsWeekInfo && slotsWeekInfo.days">
      <div
          v-for="day in slotsWeekInfo.days"
          :key="day.date"
          class="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow duration-300 border border-gray-100"
      >
        <div class="text-center mb-4">
          <h3 class="text-xl font-bold text-brand mb-1">{{ day.day }}</h3>
          <p class="text-gray-600 text-sm">{{ formatDate(day.date) }}</p>
        </div>

        <div class="mb-4">
          <p class="text-center text-sm text-gray-500">
            Доступно слотов: {{ day.total_slots }}
          </p>
        </div>

        <!-- Слоты времени -->
        <div class="grid grid-cols-2 gap-2" v-if="day.slots.length > 0">
          <button
              v-for="timeSlot in day.slots"
              :key="timeSlot"
              class="py-2 px-3 bg-brand hover text-white rounded-lg hover:bg-brand-dark transition duration-200 text-sm font-medium"
              @click="selectTimeSlot(day, timeSlot)"
          >
            {{ timeSlot }}
          </button>
        </div>

        <div v-else class="text-center py-4">
          <p class="text-gray-400 text-sm">Нет доступных слотов</p>
        </div>
      </div>
    </div>

    <!-- Состояние загрузки -->
    <div v-if="!slotsWeekInfo" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
      <p class="text-gray-600 mt-4">Загрузка доступных слотов...</p>
    </div>
  </div>
</template>