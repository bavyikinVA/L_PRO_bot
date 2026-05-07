<template>
  <section class="py-6">
    <div class="max-w-4xl mx-auto px-4">
      <button
          type="button"
          class="mb-5 text-purple-800 font-medium"
          @click="$router.push('/admin')"
      >
        ← Назад в админ-панель
      </button>

      <h1 class="text-2xl font-bold text-purple-950 mb-5">
        Список услуг
      </h1>

      <div v-if="isFetching" class="text-center text-gray-500 py-8">
        Загружаем услуги...
      </div>

      <div
          v-else-if="error"
          class="rounded-2xl bg-red-50 border border-red-100 p-5 text-red-700"
      >
        Не удалось загрузить услуги
      </div>

      <div
          v-else-if="!services?.length"
          class="rounded-2xl bg-purple-50 border border-purple-100 p-5 text-gray-600"
      >
        Услуг пока нет
      </div>

      <div v-else class="space-y-4">
        <div
            v-for="service in services"
            :key="service.id"
            class="rounded-3xl bg-white border border-purple-100 shadow-sm p-5"
        >
          <div class="flex items-start justify-between gap-4">
            <div>
              <h2 class="text-lg font-bold text-gray-900">
                {{ service.label }}
              </h2>

              <p class="text-gray-600 mt-2">
                {{ service.description }}
              </p>
            </div>

            <div class="text-right shrink-0">
              <p class="font-bold text-purple-900">
                {{ formatPrice(service.price) }} ₽
              </p>

              <p class="text-sm text-gray-500">
                {{ formatDuration(service.duration_minutes) }}
              </p>
            </div>
          </div>

          <div class="mt-4 flex gap-3">
            <button
                type="button"
                class="rounded-xl bg-purple-700 text-white px-4 py-2 text-sm font-medium hover:bg-purple-800 transition"
                @click="$router.push(`/admin/services/${service.id}/edit`)"
            >
              Изменить
            </button>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useServices } from "../../composables/useServices";

const {
  services,
  isLoading,
  errorMessage,
  loadServices,
} = useServices();

const isFetching = isLoading;
const error = computed(() => Boolean(errorMessage.value));

onMounted(async () => {
  await loadServices();
});

const formatPrice = (price: number) => {
  return new Intl.NumberFormat("ru-RU").format(price);
};

const formatDuration = (minutes: number) => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;

  if (hours > 0) {
    return `${hours} ч ${mins > 0 ? `${mins} мин` : ""}`;
  }

  return `${mins} мин`;
};
</script>