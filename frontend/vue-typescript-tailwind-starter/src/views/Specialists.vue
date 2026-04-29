<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { useFetch } from '@vueuse/core';
import { inject } from 'vue';

interface Specialist {
  id: number;
  first_name: string;
  last_name: string;
  work_experience: string;
  photo: string;
}

const BASE_SITE = inject('BASE_SITE') as string;
const route = useRoute();
const router = useRouter();
const serviceId = route.params.serviceId;

// Получаем специалистов для выбранной услуги
const {
  data: specialists,
  isFetching,
  error
} = useFetch<Specialist[]>(`${BASE_SITE}/api/services/${serviceId}/specialists`).get().json();

// Функция для выбора специалиста
const selectSpecialist = (specialistId: number) => {
  router.push(`/services/${serviceId}/specialists/${specialistId}/booking`);
};

// ИСПРАВЛЕННАЯ функция - обязательно добавляем BASE_SITE
const getPhotoUrl = (photoPath: string, specialist: Specialist) => {
  // Принудительно используем ngrok URL
  const base = "https://fd6ae8ea313e.ngrok-free.app";

  if (!photoPath) {
    return `https://via.placeholder.com/300x400/3B82F6/FFFFFF?text=${encodeURIComponent(specialist.first_name + ' ' + specialist.last_name)}`;
  }

  if (photoPath.startsWith('/app/static/')) {
    return `${base}${photoPath.replace('/app/static/', '/static/')}`;
  }

  if (photoPath.startsWith('/static/')) {
    return `${base}${photoPath}`;
  }

  return `${base}/static/images/master_${specialist.last_name}.jpg`;
};

</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Заголовок -->
    <div class="mb-8">
      <button
          @click="router.back()"
          class="flex items-center text-blue-500 hover:text-blue-600 mb-4"
      >
        <i class="fas fa-arrow-left mr-2"></i>
        Назад к услугам
      </button>
      <h1 class="text-3xl font-bold text-gray-800">Выберите специалиста</h1>
      <p class="text-gray-600 mt-2">Выберите мастера для записи</p>
    </div>

    <!-- Отладочная информация BASE_SITE -->
    <div class="mb-4 p-2 bg-yellow-100 rounded text-sm" v-if="BASE_SITE">
      <p><strong>BASE_SITE:</strong> {{ BASE_SITE }}</p>
    </div>

    <!-- Состояние загрузки -->
    <div v-if="isFetching" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      <p class="text-gray-600 mt-4">Загрузка специалистов...</p>
    </div>

    <!-- Состояние ошибки -->
    <div v-else-if="error" class="text-center py-12">
      <div class="text-red-500 text-6xl mb-4">
        <i class="fas fa-exclamation-triangle"></i>
      </div>
      <p class="text-red-500 text-xl mb-2">Ошибка загрузки специалистов</p>
      <p class="text-gray-600">{{ error.message }}</p>
    </div>

    <!-- Состояние когда нет специалистов -->
    <div v-else-if="!specialists || specialists.length === 0" class="text-center py-12">
      <div class="text-gray-400 text-6xl mb-4">
        <i class="fas fa-users"></i>
      </div>
      <p class="text-gray-500 text-xl">Нет доступных специалистов для этой услуги</p>
    </div>

    <!-- Список специалистов -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <div
          v-for="specialist in specialists"
          :key="specialist.id"
          class="bg-white rounded-xl shadow-lg overflow-hidden transition-all duration-300 hover:shadow-xl hover:scale-105 cursor-pointer border border-gray-100"
          @click="selectSpecialist(specialist.id)"
      >
        <!-- Фото специалиста -->
        <div class="relative h-64 bg-gray-100 flex items-center justify-center overflow-hidden">
          <img
              :src="getPhotoUrl(specialist.photo, specialist)"
              :alt="`${specialist.first_name} ${specialist.last_name}`"
              class="w-full h-full object-cover"
              @error="(e) => {
              console.error('Image failed to load:', getPhotoUrl(specialist.photo, specialist));
              e.target.src = `https://via.placeholder.com/300x400/3B82F6/FFFFFF?text=${encodeURIComponent(specialist.first_name + ' ' + specialist.last_name)}`;
            }"
              @load="() => console.log('Image loaded successfully:', specialist.first_name)"
          />
        </div>

        <!-- Информация о специалисте -->
        <div class="p-6">
          <h3 class="text-xl font-bold text-gray-800 mb-2">
            {{ specialist.first_name }} {{ specialist.last_name }}
          </h3>

          <div class="flex items-center text-gray-600 mb-4" v-if="specialist.work_experience">
            <i class="fas fa-briefcase mr-2 text-blue-500"></i>
            <span class="text-sm">Опыт работы: {{ specialist.work_experience }}</span>
          </div>

          <!-- Кнопка выбора -->
          <button class="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 transition-colors font-semibold">
            Выбрать
            <i class="fas fa-arrow-right ml-2"></i>
          </button>
        </div>
      </div>
    </div>

    <!-- Отладочная информация -->
    <div class="mt-8 p-4 bg-gray-100 rounded-lg" v-if="specialists">
      <p class="text-sm text-gray-600 mb-2">
        Найдено специалистов: {{ specialists.length }}
      </p>
      <details class="text-xs">
        <summary class="cursor-pointer">Отладочная информация (фото)</summary>
        <div v-for="specialist in specialists" :key="specialist.id" class="mt-2 p-2 bg-white rounded">
          <p><strong>{{ specialist.first_name }} {{ specialist.last_name }}</strong></p>
          <p>Исходный путь: {{ specialist.photo }}</p>
          <p>Сгенерированный URL: {{ getPhotoUrl(specialist.photo, specialist) }}</p>
          <p>
            <a :href="getPhotoUrl(specialist.photo, specialist)" target="_blank" class="text-blue-500 underline">
              Проверить ссылку
            </a>
          </p>
        </div>
      </details>
    </div>
  </div>
</template>