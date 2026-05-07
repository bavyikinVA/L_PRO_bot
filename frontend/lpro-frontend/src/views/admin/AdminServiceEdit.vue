<template>
  <section class="py-6">
    <div class="max-w-2xl mx-auto px-4">
      <button
          type="button"
          class="mb-5 text-purple-800 font-medium"
          @click="$router.push('/admin/services/update')"
      >
        ← Назад к выбору услуги
      </button>

      <h1 class="text-2xl font-bold text-purple-950 mb-5">
        Обновить услугу
      </h1>

      <div v-if="isLoading" class="text-center text-gray-500 py-8">
        Загружаем данные услуги...
      </div>

      <form
          v-else
          class="rounded-3xl bg-white border border-purple-100 shadow-sm p-6 space-y-5"
          @submit.prevent="updateServiceHandler"
      >
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Название услуги
          </label>
          <input
              v-model="form.label"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Описание
          </label>
          <textarea
              v-model="form.description"
              rows="4"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              required
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Цена, ₽
          </label>
          <input
              v-model.number="form.price"
              type="number"
              min="0"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Длительность, минут
          </label>
          <input
              v-model.number="form.duration_minutes"
              type="number"
              min="1"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              required
          />
        </div>

        <button
            type="submit"
            class="w-full rounded-2xl bg-purple-700 text-white py-3 font-bold hover:bg-purple-800 transition disabled:opacity-60"
            :disabled="isSubmitting"
        >
          {{ isSubmitting ? 'Сохраняем...' : 'Сохранить изменения' }}
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
import { useRoute, useRouter } from "vue-router";
import { getService, updateService } from "../../api/services";

const route = useRoute();
const router = useRouter();

const serviceId = route.params.serviceId as string;

const isLoading = ref(true);
const isSubmitting = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

const form = reactive({
  label: "",
  description: "",
  price: 0,
  duration_minutes: 0,
});

onMounted(async () => {
  try {
    const service = await getService(serviceId);

    form.label = service.label;
    form.description = service.description || "";
    form.price = service.price;
    form.duration_minutes = service.duration_minutes;
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось загрузить услугу";
  } finally {
    isLoading.value = false;
  }
});

const updateServiceHandler = async () => {
  successMessage.value = "";
  errorMessage.value = "";

  try {
    isSubmitting.value = true;

    await updateService(serviceId, {
      label: form.label,
      description: form.description,
      price: form.price,
      duration_minutes: form.duration_minutes,
    });

    successMessage.value = "Услуга успешно обновлена";

    setTimeout(() => {
      router.push("/admin/services");
    }, 700);
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось обновить услугу";
  } finally {
    isSubmitting.value = false;
  }
};
</script>