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
        Добавить услугу
      </h1>

      <form
          class="rounded-3xl bg-white border border-purple-100 shadow-sm p-6 space-y-5"
          @submit.prevent="createServiceHandler"
      >
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Название услуги
          </label>
          <input
              v-model="form.label"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              placeholder="Например: RF-лифтинг"
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
              placeholder="Краткое описание услуги"
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
              placeholder="Например: 2500"
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
              placeholder="Например: 60"
              required
          />
        </div>

        <button
            type="submit"
            class="w-full rounded-2xl bg-purple-700 text-white py-3 font-bold hover:bg-purple-800 transition disabled:opacity-60"
            :disabled="isSubmitting"
        >
          {{ isSubmitting ? 'Добавляем...' : 'Добавить услугу' }}
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
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { createService } from "../../api/services";

const router = useRouter();

const isSubmitting = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

const form = reactive({
  label: "",
  description: "",
  price: null as number | null,
  duration_minutes: null as number | null,
});

const createServiceHandler = async () => {
  successMessage.value = "";
  errorMessage.value = "";

  if (!form.label || !form.description || !form.price || !form.duration_minutes) {
    errorMessage.value = "Заполните все поля";
    return;
  }

  try {
    isSubmitting.value = true;

    await createService({
      label: form.label,
      description: form.description,
      price: form.price,
      duration_minutes: form.duration_minutes,
    });

    successMessage.value = "Услуга успешно добавлена";

    setTimeout(() => {
      router.push("/admin/services");
    }, 700);
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось добавить услугу";
  } finally {
    isSubmitting.value = false;
  }
};
</script>