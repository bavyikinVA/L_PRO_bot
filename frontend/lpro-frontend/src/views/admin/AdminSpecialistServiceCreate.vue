<template>
  <section class="py-6">
    <div class="max-w-2xl mx-auto px-4">
      <button
          type="button"
          class="mb-5 text-purple-800 font-medium"
          @click="$router.push('/admin')"
      >
        ← Назад в админ-панель
      </button>

      <h1 class="text-2xl font-bold text-purple-950 mb-5">
        Привязать услугу к мастеру
      </h1>

      <form
          class="rounded-3xl bg-white border border-purple-100 shadow-sm p-6 space-y-5"
          @submit.prevent="attachService"
      >
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Мастер
          </label>
          <select
              v-model.number="form.specialist_id"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500 bg-white"
              required
          >
            <option disabled :value="0">Выберите мастера</option>
            <option
                v-for="specialist in specialists"
                :key="specialist.id"
                :value="specialist.id"
            >
              {{ specialist.first_name }} {{ specialist.last_name }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Услуга
          </label>
          <select
              v-model.number="form.service_id"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500 bg-white"
              required
          >
            <option disabled :value="0">Выберите услугу</option>
            <option
                v-for="service in services"
                :key="service.id"
                :value="service.id"
            >
              {{ service.label }} — {{ service.price }} ₽
            </option>
          </select>
        </div>

        <button
            type="submit"
            class="w-full rounded-2xl bg-purple-700 text-white py-3 font-bold hover:bg-purple-800 transition disabled:opacity-60"
            :disabled="isSubmitting || !form.specialist_id || !form.service_id"
        >
          {{ isSubmitting ? 'Привязываем...' : 'Привязать услугу' }}
        </button>

        <div
            v-if="successMessage"
            class="rounded-2xl bg-green-50 border border-green-100 p-4 text-green-700 text-center"
        >
          {{ successMessage }}
        </div>

        <div
            v-if="errorMessage"
            class="rounded-2xl bg-red-50 border border-red-100 p-4 text-red-700 text-center"
        >
          {{ errorMessage }}
        </div>
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { attachServiceToSpecialist } from "../../api/specialists";
import { useSpecialists } from "../../composables/useSpecialists";
import { useServices } from "../../composables/useServices";

const {
  specialists,
  loadSpecialists,
} = useSpecialists();

const {
  services,
  loadServices,
} = useServices();

const isSubmitting = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

const form = reactive({
  specialist_id: 0,
  service_id: 0,
});

onMounted(async () => {
  try {
    await Promise.all([
      loadSpecialists(),
      loadServices(),
    ]);
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось загрузить мастеров или услуги";
  }
});

const attachService = async () => {
  successMessage.value = "";
  errorMessage.value = "";

  try {
    isSubmitting.value = true;

    await attachServiceToSpecialist({
      specialist_id: form.specialist_id,
      service_id: form.service_id,
    });

    successMessage.value = "Услуга успешно привязана к мастеру";
    form.service_id = 0;
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось привязать услугу к мастеру";
  } finally {
    isSubmitting.value = false;
  }
};
</script>