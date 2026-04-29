<script setup lang="ts">
import { useFetch } from '@vueuse/core';
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { inject } from 'vue';
import ServiceCard from '../components/Services.vue';

interface Service {
  id: number;
  label: string;
  description: string;
  price: number;
  duration_minutes: number;
}

const BASE_SITE = inject('BASE_SITE') as string;
const searchQuery = ref<string>('');

console.log('BASE_SITE:', BASE_SITE); // Отладка

// Запрос всех услуг
const {
  data: services,
  isFetching,
  error,
  execute
} = useFetch<Service[]>(`${BASE_SITE}/api/services`, {
  immediate: true // Убедимся что запрос выполняется сразу
}).get().json();

// Отладка состояния
console.log('isFetching:', isFetching.value);
console.log('error:', error.value);
console.log('services:', services.value);

// Добавляем иконки для услуг
const getServiceIcon = (serviceId: number, serviceLabel: string) => {
  const iconMap: { [key: string]: string } = {
    'чистка': 'fas fa-spa',
    'лифтинг': 'fas fa-leaf',
    'массаж': 'fas fa-hand-holding-heart',
    'уход': 'fas fa-seedling',
    'процедура': 'fas fa-magic',
    'ультразвуковая': 'fas fa-spa',
    'rf': 'fas fa-leaf'
  };

  const label = serviceLabel.toLowerCase();
  for (const [keyword, icon] of Object.entries(iconMap)) {
    if (label.includes(keyword)) {
      return icon;
    }
  }

  return 'fas fa-star';
};

// Форматируем услуги с иконками
const formattedServices = computed(() => {
  if (!services.value) return [];

  console.log('Formatted services:', services.value); // Отладка

  return services.value.map(service => ({
    ...service,
    icon: getServiceIcon(service.id, service.label)
  }));
});

// Фильтруем услуги
const filteredServices = computed(() => {
  if (!formattedServices.value) return [];

  const query = searchQuery.value.toLowerCase().trim();
  if (!query) return formattedServices.value;

  return formattedServices.value.filter((service: Service) => {
    return (
        service.label.toLowerCase().includes(query) ||
        service.description.toLowerCase().includes(query)
    );
  });
});

// Обработчик клика по документу
const handleClickOutside = (event: MouseEvent) => {
  const inputElement = document.getElementById('search');
  if (inputElement && !inputElement.contains(event.target as Node)) {
    inputElement.blur();
  }
};

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
  console.log('Component mounted'); // Отладка
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
  <div class="mb-12 mt-5">
    <div class="relative max-w-xl mx-auto">
      <input
          v-model="searchQuery"
          type="text"
          id="search"
          placeholder="Поиск услуги..."
          class="w-full px-4 py-3 rounded-lg shadow-sm border border-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
      />
      <button class="absolute right-3 top-3 text-gray-400">
        <i class="fas fa-search"></i>
      </button>
    </div>
  </div>

  <div>
    <!-- Отладка информации -->
    <div v-if="BASE_SITE" class="text-center text-sm text-gray-400 mb-4">
      Base URL: {{ BASE_SITE }}
    </div>

    <!-- Состояние загрузки -->
    <div v-if="isFetching" class="text-center py-8">
      <p class="text-lg text-gray-600">Загрузка услуг...</p>
    </div>

    <!-- Состояние ошибки -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-red-500 text-lg">Ошибка загрузки услуг</p>
      <p class="text-gray-600 mt-2">{{ error.message }}</p>
      <button
          @click="execute()"
          class="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Повторить
      </button>
    </div>

    <!-- Состояние когда нет услуг -->
    <div v-else-if="!filteredServices.length && searchQuery" class="text-center py-8">
      <p class="text-gray-500 text-lg">Услуги по запросу "{{ searchQuery }}" не найдены</p>
    </div>

    <!-- Состояние когда вообще нет услуг -->
    <div v-else-if="!filteredServices.length" class="text-center py-8">
      <p class="text-gray-500 text-lg">Нет доступных услуг</p>
    </div>

    <!-- Отображение услуг -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <ServiceCard
          v-for="service in filteredServices"
          :key="service.id"
          :label="service.label"
          :description="service.description"
          :price="service.price"
          :duration="service.duration_minutes"
          :icon="service.icon"
          :specialId="service.id"
      />
    </div>
  </div>
</template>