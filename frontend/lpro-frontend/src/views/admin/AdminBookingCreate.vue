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
        Записать клиента вручную
      </h1>

      <form
          class="rounded-3xl bg-white border border-purple-100 shadow-sm p-6 space-y-5"
          @submit.prevent="createBookingHandler"
      >
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Клиент
          </label>

          <select
              v-model.number="form.user_id"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 bg-white outline-none focus:border-purple-500"
              required
          >
            <option disabled :value="0">Выберите клиента</option>
            <option
                v-for="user in users"
                :key="user.id"
                :value="user.id"
            >
              {{ getUserLabel(user) }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Мастер
          </label>

          <select
              v-model.number="form.specialist_id"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 bg-white outline-none focus:border-purple-500"
              required
              @change="loadSpecialistServices"
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
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 bg-white outline-none focus:border-purple-500"
              required
              :disabled="!form.specialist_id"
              @change="resetCalendar"
          >
            <option disabled :value="0">
              {{ form.specialist_id ? 'Выберите услугу' : 'Сначала выберите мастера' }}
            </option>

            <option
                v-for="service in services"
                :key="service.id"
                :value="service.id"
            >
              {{ service.label }} — {{ service.price }} ₽, {{ service.duration_minutes }} мин
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Дата
          </label>

          <div
              v-if="!form.specialist_id || !form.service_id"
              class="rounded-2xl bg-purple-50 border border-purple-100 p-4 text-gray-600 text-center"
          >
            Сначала выберите мастера и услугу
          </div>

          <div v-else class="rounded-3xl border border-purple-100 bg-white p-3">
            <VDatePicker
                v-model="selectedDate"
                mode="date"
                :min-date="new Date()"
                :attributes="calendarAttributes"
                expanded
                transparent
                borderless
                @update:model-value="onDateSelected"
            />

            <div class="mt-3 flex flex-col gap-2 text-sm">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-purple-500"></span>
                <span class="text-gray-600">Есть свободные слоты</span>
              </div>

              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full bg-gray-300"></span>
                <span class="text-gray-600">Нет свободных слотов</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="slots.length">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Время
          </label>

          <div class="grid grid-cols-3 gap-3">
            <button
                v-for="slot in slots"
                :key="slot"
                type="button"
                class="rounded-2xl border px-4 py-3 font-medium transition"
                :class="form.time === slot
                  ? 'bg-purple-700 text-white border-purple-700'
                  : 'bg-white text-purple-900 border-purple-100 hover:bg-purple-50'"
                @click="form.time = slot"
            >
              {{ slot }}
            </button>
          </div>
        </div>

        <div
            v-else-if="form.specialist_id && form.service_id && form.date && slotsLoaded"
            class="rounded-2xl bg-purple-50 border border-purple-100 p-4 text-gray-600 text-center"
        >
          На выбранную дату свободных слотов нет
        </div>

        <button
            type="submit"
            class="w-full rounded-2xl bg-purple-700 text-white py-3 font-bold hover:bg-purple-800 transition disabled:opacity-60"
            :disabled="isSubmitting || !canSubmit"
        >
          {{ isSubmitting ? 'Создаём запись...' : 'Создать запись' }}
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
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import type { Service, SlotsResponse, User } from "../../types/models";
import { getSpecialistServices } from "../../api/specialists";
import { createBooking, getAvailableSlots } from "../../api/adminBookings";
import { useSpecialists } from "../../composables/useSpecialists";
import { useAdminUsers } from "../../composables/useAdminUsers";

const router = useRouter();

const {
  users,
  loadUsers,
} = useAdminUsers();

const {
  specialists,
  loadSpecialists,
} = useSpecialists();
const services = ref<Service[]>([]);
const slots = ref<string[]>([]);

const selectedDate = ref<Date | null>(null);
const availableDates = ref<string[]>([]);
const unavailableDates = ref<string[]>([]);
const slotsLoaded = ref(false);

const isSubmitting = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

const form = reactive({
  user_id: 0,
  specialist_id: 0,
  service_id: 0,
  date: "",
  time: "",
});

const canSubmit = computed(() => {
  return Boolean(
      form.user_id &&
      form.specialist_id &&
      form.service_id &&
      form.date &&
      form.time
  );
});

const calendarAttributes = computed(() => [
  {
    key: "available",
    dates: availableDates.value.map(fromDateString),
    highlight: {
      color: "purple",
      fillMode: "light",
    },
    dot: {
      color: "purple",
    },
  },
  {
    key: "unavailable",
    dates: unavailableDates.value.map(fromDateString),
    highlight: {
      color: "gray",
      fillMode: "light",
    },
  },
]);

onMounted(async () => {
  try {
    await Promise.all([
      loadUsers(),
      loadSpecialists(),
    ]);
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось загрузить данные для формы";
  }
});

const loadSpecialistServices = async () => {
  errorMessage.value = "";
  form.service_id = 0;
  services.value = [];
  resetCalendar();

  if (!form.specialist_id) return;

  try {
    services.value = await getSpecialistServices(form.specialist_id);
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось загрузить услуги мастера";
  }
};

const resetCalendar = () => {
  selectedDate.value = null;
  form.date = "";
  form.time = "";
  slots.value = [];
  availableDates.value = [];
  unavailableDates.value = [];
  slotsLoaded.value = false;
};

const onDateSelected = async (date: Date | null) => {
  if (!date) return;

  form.date = toDateString(date);
  await loadSlots();
};

const loadSlots = async () => {
  errorMessage.value = "";
  form.time = "";
  slots.value = [];
  slotsLoaded.value = false;
  availableDates.value = [];
  unavailableDates.value = [];

  if (!form.specialist_id || !form.service_id || !form.date) return;

  try {
    const data: SlotsResponse = await getAvailableSlots(
        form.specialist_id,
        form.date,
        form.service_id
    );

    availableDates.value = data.days
        .filter((item) => item.slots.length > 0)
        .map((item) => item.date);

    unavailableDates.value = data.days
        .filter((item) => item.slots.length === 0)
        .map((item) => item.date);

    const selectedDay = data.days.find((item) => item.date === form.date);

    slots.value = selectedDay?.slots || [];
    slotsLoaded.value = true;
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось загрузить свободные слоты";
  }
};

const toDateString = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
};

const fromDateString = (dateString: string) => {
  const [year, month, day] = dateString.split("-").map(Number);
  return new Date(year, month - 1, day);
};

const getUserLabel = (user: User) => {
  const fullName = [
    user.last_name,
    user.first_name,
    user.patronymic,
  ].filter(Boolean).join(" ");

  return `${fullName || "Без имени"} — ${user.phone_number || "без телефона"}`;
};

const getSelectedServiceDuration = () => {
  const selectedService = services.value.find((service) => service.id === form.service_id);
  return selectedService?.duration_minutes || 120;
};

const createBookingHandler = async () => {
  successMessage.value = "";
  errorMessage.value = "";

  if (!canSubmit.value) {
    errorMessage.value = "Заполните все поля";
    return;
  }

  try {
    isSubmitting.value = true;

    const bookingDatetime = `${form.date}T${form.time}:00+03:00`;

    await createBooking({
      specialist_id: form.specialist_id,
      user_id: form.user_id,
      service_id: form.service_id,
      booking_datetime: bookingDatetime,
      status: "confirmed",
      duration_minutes: getSelectedServiceDuration(),
      is_cancelled: false,
    });

    successMessage.value = "Клиент успешно записан";

    setTimeout(() => {
      router.push("/admin");
    }, 900);
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось создать запись";
  } finally {
    isSubmitting.value = false;
  }
};
</script>