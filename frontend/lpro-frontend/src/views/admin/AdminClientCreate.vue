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
        Добавить клиента
      </h1>

      <form
          class="rounded-3xl bg-white border border-purple-100 shadow-sm p-6 space-y-5"
          @submit.prevent="createClient"
      >
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Фамилия
          </label>
          <input
              v-model="form.last_name"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              placeholder="Иванов"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Имя
          </label>
          <input
              v-model="form.first_name"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              placeholder="Иван"
              required
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Отчество
          </label>
          <input
              v-model="form.patronymic"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              placeholder="Иванович"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Телефон
          </label>
          <input
              v-model="form.phone_number"
              type="text"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
              placeholder="89XXXXXXXXX"
              required
          />
          <p class="text-sm text-gray-500 mt-2">
            Формат: 11 цифр, начинается с 89
          </p>
        </div>

        <button
            type="submit"
            class="w-full rounded-2xl bg-purple-700 text-white py-3 font-bold hover:bg-purple-800 transition disabled:opacity-60"
            :disabled="isSubmitting"
        >
          {{ isSubmitting ? 'Добавляем...' : 'Добавить клиента' }}
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
import { inject, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { getTelegramInitData } from "../../api/admin";

const router = useRouter();
const BASE_SITE = inject("BASE_SITE", "") as string;

const isSubmitting = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

const form = reactive({
  first_name: "",
  last_name: "",
  patronymic: "",
  phone_number: "",
});

const createClient = async () => {
  successMessage.value = "";
  errorMessage.value = "";

  if (!/^89\d{9}$/.test(form.phone_number)) {
    errorMessage.value = "Введите телефон в формате 89XXXXXXXXX";
    return;
  }

  try {
    isSubmitting.value = true;

    const response = await fetch(`${BASE_SITE}/api/admin/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": getTelegramInitData(),
      },
      body: JSON.stringify({
        telegram_id: null,
        username: null,
        first_name: form.first_name,
        last_name: form.last_name,
        patronymic: form.patronymic || null,
        phone_number: form.phone_number,
        is_admin: false,
      }),
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    successMessage.value = "Клиент успешно добавлен";

    setTimeout(() => {
      router.push("/admin");
    }, 700);
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось добавить клиента";
  } finally {
    isSubmitting.value = false;
  }
};
</script>