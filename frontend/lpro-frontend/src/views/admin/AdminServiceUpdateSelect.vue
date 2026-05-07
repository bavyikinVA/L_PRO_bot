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
        Выберите услугу для обновления
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

      <div v-else class="space-y-4">
        <button
            v-for="service in services"
            :key="service.id"
            type="button"
            class="w-full rounded-3xl bg-white border border-purple-100 shadow-sm p-5 text-left hover:bg-purple-50 transition"
            @click="$router.push(`/admin/services/${service.id}/edit`)"
        >
          <div class="flex justify-between gap-4">
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
                {{ service.price }} ₽
              </p>

              <p class="text-sm text-gray-500">
                {{ service.duration_minutes }} мин
              </p>
            </div>
          </div>
        </button>
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
</script>