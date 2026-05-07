<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { useFetch } from '@vueuse/core';
import { inject } from 'vue';
import { getPhotoUrl } from "../utils/getPhotoUrl";

import type {Specialist} from "../types/models";

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

</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Заголовок -->
    <div class="mb-8">
      <button
          @click="router.back()"
          class="flex items-center text-brand hover:text-brand-dark mb-4">
        <i class="fas fa-arrow-left mr-2"></i>
        Назад к услугам
      </button>
      <h1 class="text-3xl mt-2 text-gray-800">Выберите мастера для записи</h1>

    </div>

    <!-- Состояние загрузки -->
    <div v-if="isFetching" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-brand"></div>
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
              :src="getPhotoUrl(specialist.photo)"
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
          <h3 class="text-xl text-gray-800 mt-2">
            {{ specialist.first_name }} {{ specialist.last_name }}
          </h3>

          <div class="flex items-center text-gray-600 mb-4" v-if="specialist.work_experience">
            <i class="fas fa-briefcase mr-2 text-brand"></i>
            <span class="text-sm">Опыт работы: {{ specialist.work_experience }}</span>
          </div>

          <!-- Кнопка выбора -->
          <button class="w-full bg-brand hover text-white py-3 rounded-lg hover:bg-brand-dark transition-colors font-semibold">
            Выбрать
            <i class="fas fa-arrow-right ml-2"></i>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>