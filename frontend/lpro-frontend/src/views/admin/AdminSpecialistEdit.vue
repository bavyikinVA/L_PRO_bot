<template>
  <section class="py-6">
    <div class="max-w-2xl mx-auto px-4">
      <button
          type="button"
          class="mb-5 text-purple-800 font-medium"
          @click="$router.push('/admin/specialists/update')"
      >
        ← Назад к выбору мастера
      </button>

      <h1 class="text-2xl font-bold text-purple-950 mb-5">
        Изменить данные мастера
      </h1>

      <div v-if="isLoading" class="text-center text-gray-500 py-8">
        Загружаем данные мастера...
      </div>

      <div
          v-if="errorMessage"
          class="rounded-2xl bg-red-50 border border-red-100 p-4 text-red-700 text-center mb-4"
      >
        {{ errorMessage }}
      </div>

      <form
          v-if="!isLoading && !errorMessage"
          class="rounded-3xl bg-white border border-purple-100 shadow-sm p-6 space-y-5"
          @submit.prevent="updateSpecialistHandler"
      >
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Имя</label>
          <input
              v-model="form.first_name"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Фамилия</label>
          <input
              v-model="form.last_name"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Опыт работы</label>
          <input
              v-model="form.work_experience"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Фото</label>
          <input
              v-model="form.photo"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              required
          />
        </div>

        <div v-if="form.photo" class="rounded-2xl bg-purple-50 p-4">
          <p class="text-sm text-gray-600 mb-3">Предпросмотр фото:</p>

          <img
              :src="getPhotoUrl(form.photo)"
              alt=""
              class="w-32 h-32 rounded-2xl object-cover"
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
      </form>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { Specialist } from "../../types/models";
import { getSpecialist, updateSpecialist } from "../../api/specialists";
import { getPhotoUrl } from "../../utils/getPhotoUrl";

const route = useRoute();
const router = useRouter();

const specialistId = route.params.specialistId as string;

const isLoading = ref(true);
const isSubmitting = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

const form = reactive({
  first_name: "",
  last_name: "",
  work_experience: "",
  photo: "",
});

onMounted(async () => {
  try {
    const specialist: Specialist = await getSpecialist(specialistId);

    form.first_name = specialist.first_name;
    form.last_name = specialist.last_name;
    form.work_experience = specialist.work_experience || "";
    form.photo = specialist.photo || "";
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось загрузить данные мастера";
  } finally {
    isLoading.value = false;
  }
});

const updateSpecialistHandler = async () => {
  successMessage.value = "";
  errorMessage.value = "";

  try {
    isSubmitting.value = true;

    await updateSpecialist(specialistId, {
      first_name: form.first_name,
      last_name: form.last_name,
      work_experience: form.work_experience,
      photo: form.photo,
    });

    successMessage.value = "Данные мастера успешно обновлены";

    setTimeout(() => {
      router.push("/admin/specialists/update");
    }, 700);
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось обновить данные мастера";
  } finally {
    isSubmitting.value = false;
  }
};
</script>