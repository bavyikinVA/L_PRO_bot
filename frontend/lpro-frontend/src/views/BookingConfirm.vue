<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { useFetch } from '@vueuse/core';
import {ref, computed, inject} from 'vue';

interface BookingData {
  specialist_id: number;
  user_id: number;  // Используем внутренний ID пользователя
  service_id: number;
  booking_datetime: string;
  duration_minutes: number;
}

const BASE_SITE = inject('BASE_SITE') as string;
const route = useRoute();
const router = useRouter();

// Получаем ВСЕ параметры из URL
const specialistId = parseInt(route.query.specialist_id as string);
const serviceId = parseInt(route.query.service_id as string);
const bookingDate = route.query.date as string;
const bookingTime = route.query.time as string;
const TG_USER_ID = route.query.tg_user_id as string; // Получаем из URL

console.log('URL Parameters:', {
  specialistId,
  serviceId,
  bookingDate,
  bookingTime,
  TG_USER_ID
});

// Получаем информацию о специалисте
const { data: specialist } = useFetch(
    `${BASE_SITE}/api/specialists/${specialistId}`
).get().json();

// Получаем информацию об услуге
const { data: service } = useFetch(
    `${BASE_SITE}/api/services/${serviceId}`
).get().json();

// Получаем ID пользователя по Telegram ID
const { data: userId, error: userIdError, isFetching: isUserIdLoading } = useFetch<number>(
    `${BASE_SITE}/api/user/${TG_USER_ID}`
).get().json();

// Проверяем успешность получения user_id
const isUserIdReady = computed(() => {
  return !isUserIdLoading.value && userId.value && !userIdError.value;
});

// Состояния модальных окон
const isConfirmationModalOpen = ref(true);
const isSuccessModalOpen = ref(false);
const isErrorModalOpen = ref(false);
const isLoading = ref(false);

// Форматируем дату и время
const formatDateTime = () => {
  const date = new Date(bookingDate);
  const formattedDate = date.toLocaleDateString('ru-RU', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  return `${formattedDate} в ${bookingTime}`;
};

// Создаем бронирование
const createBooking = async () => {
  // Проверяем что user_id получен
  if (!isUserIdReady.value) {
    console.error('User ID not available');
    isErrorModalOpen.value = true;
    return;
  }

  isLoading.value = true;

  try {
    const bookingDateTime = new Date(`${bookingDate}T${bookingTime}:00+03:00`).toISOString();

    const bookingData: BookingData = {
      specialist_id: specialistId,
      user_id: userId.value!,  // Используем полученный внутренний ID
      service_id: serviceId,
      booking_datetime: bookingDateTime,
    };

    const response = await fetch(`${BASE_SITE}/api/bookings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(bookingData)
    });

    if (!response.ok) {
      throw new Error('Ошибка при создании бронирования');
    }

    isConfirmationModalOpen.value = false;
    isSuccessModalOpen.value = true;

  } catch (error) {
    console.error('Booking error:', error);
    isConfirmationModalOpen.value = false;
    isErrorModalOpen.value = true;
  } finally {
    isLoading.value = false;
  }
};

const closeConfirmationModal = () => {
  router.back();
};

const closeSuccessModal = () => {
  router.push('/');
};

const closeErrorModal = () => {
  isErrorModalOpen.value = false;
  router.back();
};
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <!-- Модальное окно подтверждения -->
    <div v-if="isConfirmationModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div class="bg-white rounded-lg shadow-lg w-96 p-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-4 text-center">
          Подтверждение записи
        </h2>

        <!-- Состояние загрузки user_id -->
        <div v-if="isUserIdLoading" class="text-center py-4">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-brand"></div>
          <p class="text-gray-600 mt-2 text-sm">Загрузка данных...</p>
        </div>

        <!-- Ошибка получения user_id -->
        <div v-else-if="userIdError" class="text-center py-4 text-red-500">
          <p>Ошибка загрузки данных пользователя</p>
        </div>

        <!-- Основной контент -->
        <div v-else-if="isUserIdReady">
          <div class="mb-6">
            <p class="text-gray-700 mb-2">
              <strong>Специалист:</strong> {{ specialist?.first_name }} {{ specialist?.last_name }}
            </p>
            <p class="text-gray-700 mb-2">
              <strong>Услуга:</strong> {{ service?.label }}
            </p>
            <p class="text-gray-700 mb-2">
              <strong>Дата и время:</strong> {{ formatDateTime() }}
            </p>
            <p class="text-gray-700">
              <strong>Длительность:</strong> {{ service?.duration_minutes }} минут
            </p>
          </div>

          <div class="flex justify-around">
            <button
                class="py-2 px-6 bg-brand hover text-white rounded-lg hover:bg-brand-dark transition duration-200 disabled:opacity-50"
                @click="createBooking"
                :disabled="isLoading"
            >
              {{ isLoading ? 'Запись...' : 'Подтвердить' }}
            </button>
            <button
                class="py-2 px-6 bg-red-500 text-white rounded-lg hover:bg-red-600 transition duration-200"
                @click="closeConfirmationModal"
            >
              Отмена
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно успешной записи -->
    <div v-if="isSuccessModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div class="bg-white rounded-lg shadow-lg w-96 p-6">
        <div class="text-center mb-4">
          <i class="fas fa-check-circle text-brand text-5xl mb-4"></i>
          <h2 class="text-2xl font-bold text-brand mb-2">Запись успешно создана!</h2>
        </div>

        <div class="mb-6 text-center">
          <p class="text-gray-700 mb-2">
            Вы записаны к <strong>{{ specialist?.first_name }} {{ specialist?.last_name }}</strong>
          </p>
          <p class="text-gray-700 mb-2">
            на услугу <strong>{{ service?.label }}</strong>
          </p>
          <p class="text-gray-700">
            <strong>{{ formatDateTime() }}</strong>
          </p>
        </div>

        <button
            class="w-full py-3 bg-brand text-white rounded-lg hover:bg-brand-dark transition duration-200 font-semibold"
            @click="closeSuccessModal"
        >
          Вернуться на главную
        </button>
      </div>
    </div>

    <!-- Модальное окно ошибки -->
    <div v-if="isErrorModalOpen" class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div class="bg-white rounded-lg shadow-lg w-96 p-6">
        <div class="text-center mb-4">
          <i class="fas fa-exclamation-triangle text-red-500 text-5xl mb-4"></i>
          <h2 class="text-2xl font-bold text-red-600 mb-2">Ошибка записи</h2>
        </div>

        <p class="text-gray-700 text-center mb-6">
          Произошла ошибка при создании записи. Пожалуйста, попробуйте позже.
        </p>

        <button
            class="w-full py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition duration-200"
            @click="closeErrorModal"
        >
          Назад
        </button>
      </div>
    </div>
  </div>
</template>