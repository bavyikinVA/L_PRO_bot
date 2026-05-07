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
        Выберите мастера для изменения
      </h1>

      <div v-if="isFetching" class="text-center text-gray-500 py-8">
        Загружаем мастеров...
      </div>

      <div
          v-else-if="error"
          class="rounded-2xl bg-red-50 border border-red-100 p-5 text-red-700"
      >
        Не удалось загрузить мастеров
      </div>

      <div v-else class="space-y-4">
        <button
            v-for="specialist in specialists"
            :key="specialist.id"
            type="button"
            class="w-full rounded-3xl bg-white border border-purple-100 shadow-sm p-5 text-left hover:bg-purple-50 transition"
            @click="$router.push(`/admin/specialists/${specialist.id}/edit`)">
          <div class="flex items-center gap-4">
            <img
                v-if="specialist.photo"
                :src="getPhotoUrl(specialist.photo)"
                alt=""
                class="w-16 h-16 rounded-2xl object-cover bg-purple-50"
            />

            <div>
              <h2 class="text-lg font-bold text-gray-900">
                {{ specialist.first_name }} {{ specialist.last_name }}
              </h2>

              <p class="text-gray-600 mt-1">
                Опыт: {{ specialist.work_experience || 'не указан' }}
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
import { useSpecialists } from "../../composables/useSpecialists";
import { getPhotoUrl } from "../../utils/getPhotoUrl";

const {
  specialists,
  isLoading,
  errorMessage,
  loadSpecialists,
} = useSpecialists();

const isFetching = isLoading;
const error = computed(() => Boolean(errorMessage.value));

onMounted(async () => {
  await loadSpecialists();
});
</script>