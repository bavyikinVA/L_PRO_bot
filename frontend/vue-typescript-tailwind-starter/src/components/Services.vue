<script setup lang="ts">
import { useRouter } from "vue-router";

interface Props {
  label: string;
  description: string;
  price: number;
  duration: number;
  icon: string;
  specialId: number;
}

const props = defineProps<Props>();

const router = useRouter();

const handleBook = () => {
  console.log('Booking service:', props.specialId);
  router.push(`/services/${props.specialId}/specialists`);
};

const formatPrice = (price: number) => {
  return new Intl.NumberFormat('ru-RU').format(price);
};

const formatDuration = (minutes: number) => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;

  if (hours > 0) {
    return `${hours} ч ${mins > 0 ? `${mins} мин` : ''}`;
  }
  return `${mins} мин`;
};
</script>

<template>
  <div
      class="bg-white rounded-xl shadow-lg overflow-hidden transition-transform duration-300 hover:scale-105 flex flex-col items-center justify-center p-6 h-full"
  >
    <div
        class="bg-blue-100 rounded-full p-6 w-28 h-28 flex items-center justify-center mb-4"
    >
      <i :class="icon + ' text-blue-600 text-4xl'" aria-hidden="true"></i>
    </div>

    <h3 class="text-xl font-bold text-gray-800 mb-2 text-center">{{ label }}</h3>

    <p class="text-gray-600 mb-3 text-center flex-grow">
      {{ description }}
    </p>

    <div class="flex justify-between w-full mb-4 text-sm text-gray-500">
      <span class="flex items-center">
        <i class="fas fa-clock mr-1"></i>
        {{ formatDuration(duration) }}
      </span>
      <span class="flex items-center font-semibold text-green-600">
        <i class="fas fa-tag mr-1"></i>
        {{ formatPrice(price) }} ₽
      </span>
    </div>

    <button
        @click="handleBook"
        class="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors w-full"
    >
      Записаться
    </button>
  </div>
</template>