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
        Добавить мастера
      </h1>

      <form
          class="rounded-3xl bg-white border border-purple-100 shadow-sm p-6 space-y-5"
          @submit.prevent="createSpecialistHandler"
      >
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Имя
          </label>
          <input
              v-model="form.first_name"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              placeholder="Например: Анна"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Фамилия
          </label>
          <input
              v-model="form.last_name"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              placeholder="Например: Иванова"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Опыт работы
          </label>
          <input
              v-model="form.work_experience"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              placeholder="Например: 5 лет"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Ссылка на фото
          </label>
          <input
              v-model="form.photo"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              placeholder="https://..."
              required
          />
        </div>

        <button
            type="submit"
            class="w-full rounded-2xl bg-purple-700 text-white py-3 font-bold hover:bg-purple-800 transition disabled:opacity-60"
            :disabled="isSubmitting"
        >
          {{ isSubmitting ? 'Добавляем...' : 'Добавить мастера' }}
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
import { createSpecialist } from "../../api/specialists";

const router = useRouter();

const isSubmitting = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

const form = reactive({
  first_name: "",
  last_name: "",
  work_experience: "",
  photo: "",
});

const createSpecialistHandler = async () => {
  successMessage.value = "";
  errorMessage.value = "";

  try {
    isSubmitting.value = true;

    await createSpecialist({
      first_name: form.first_name,
      last_name: form.last_name,
      work_experience: form.work_experience,
      photo: form.photo,
    });

    successMessage.value = "Мастер успешно добавлен";

    setTimeout(() => {
      router.push("/admin");
    }, 700);
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось добавить мастера";
  } finally {
    isSubmitting.value = false;
  }
};
</script>