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
        Сгенерировать рабочее время мастера
      </h1>

      <form
          class="rounded-3xl bg-white border border-purple-100 shadow-sm p-6 space-y-5"
          @submit.prevent="generateScheduleHandler"
      >
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Мастер
          </label>

          <select
              v-model.number="form.specialist_id"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 bg-white outline-none focus:border-purple-500"
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

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Месяц
            </label>

            <select
                v-model.number="form.target_month"
                class="w-full rounded-2xl border border-purple-100 px-4 py-3 bg-white outline-none focus:border-purple-500"
                required
            >
              <option
                  v-for="month in months"
                  :key="month.value"
                  :value="month.value"
              >
                {{ month.label }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Год
            </label>

            <input
                v-model.number="form.target_year"
                type="number"
                min="2024"
                max="2100"
                class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
                required
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-3">
            Рабочие дни
          </label>

          <div class="grid grid-cols-2 gap-3">
            <button
                v-for="day in days"
                :key="day.code"
                type="button"
                class="rounded-2xl border px-4 py-3 font-medium transition"
                :class="form.working_days.includes(day.code)
                  ? 'bg-purple-700 text-white border-purple-700'
                  : 'bg-white text-purple-900 border-purple-100 hover:bg-purple-50'"
                @click="toggleDay(day.code)"
            >
              {{ day.label }}
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Начало
            </label>

            <input
                v-model="form.start_time"
                type="time"
                class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
                required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Конец
            </label>

            <input
                v-model="form.end_time"
                type="time"
                class="w-full rounded-2xl border border-purple-100 px-4 py-3 outline-none focus:border-purple-500"
                required
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Интервал между слотами
          </label>

          <select
              v-model.number="form.slot_duration_minutes"
              class="w-full rounded-2xl border border-purple-100 px-4 py-3 bg-white outline-none focus:border-purple-500"
              required
          >
            <option :value="30">30 минут</option>
            <option :value="60">60 минут</option>
            <option :value="90">90 минут</option>
            <option :value="120">120 минут</option>
          </select>
        </div>

        <button
            type="submit"
            class="w-full rounded-2xl bg-purple-700 text-white py-3 font-bold hover:bg-purple-800 transition disabled:opacity-60"
            :disabled="isSubmitting || !canSubmit"
        >
          {{ isSubmitting ? 'Генерируем...' : 'Сгенерировать расписание' }}
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
import { useSpecialists } from "../../composables/useSpecialists";
import { generateSchedule } from "../../api/schedules";

const {specialists, loadSpecialists} = useSpecialists();

onMounted(async () => {await loadSpecialists();});
const isSubmitting = ref(false);
const successMessage = ref("");
const errorMessage = ref("");

const now = new Date();

const form = reactive({
  specialist_id: 0,
  target_month: now.getMonth() + 1,
  target_year: now.getFullYear(),
  working_days: [] as string[],
  start_time: "09:00",
  end_time: "18:00",
  slot_duration_minutes: 120,
});

const days = [
  { code: "mon", label: "Понедельник" },
  { code: "tue", label: "Вторник" },
  { code: "wed", label: "Среда" },
  { code: "thu", label: "Четверг" },
  { code: "fri", label: "Пятница" },
  { code: "sat", label: "Суббота" },
  { code: "sun", label: "Воскресенье" },
];

const months = [
  { value: 1, label: "Январь" },
  { value: 2, label: "Февраль" },
  { value: 3, label: "Март" },
  { value: 4, label: "Апрель" },
  { value: 5, label: "Май" },
  { value: 6, label: "Июнь" },
  { value: 7, label: "Июль" },
  { value: 8, label: "Август" },
  { value: 9, label: "Сентябрь" },
  { value: 10, label: "Октябрь" },
  { value: 11, label: "Ноябрь" },
  { value: 12, label: "Декабрь" },
];

const canSubmit = computed(() => {
  return Boolean(
      form.specialist_id &&
      form.working_days.length &&
      form.start_time &&
      form.end_time &&
      form.start_time < form.end_time
  );
});

const toggleDay = (dayCode: string) => {
  if (form.working_days.includes(dayCode)) {
    form.working_days = form.working_days.filter((item) => item !== dayCode);
  } else {
    form.working_days.push(dayCode);
  }
};

const generateScheduleHandler = async () => {
  successMessage.value = "";
  errorMessage.value = "";

  if (!canSubmit.value) {
    errorMessage.value = "Заполните все поля корректно";
    return;
  }

  try {
    isSubmitting.value = true;

    const result = await generateSchedule({
      specialist_id: form.specialist_id,
      working_days: form.working_days,
      start_time: form.start_time,
      end_time: form.end_time,
      slot_duration_minutes: form.slot_duration_minutes,
      target_month: form.target_month,
      target_year: form.target_year,
    });

    successMessage.value = `Расписание успешно ${result.action}. Обработано дней: ${result.processed_days}`;
  } catch (error) {
    console.error(error);
    errorMessage.value = "Не удалось сгенерировать расписание";
  } finally {
    isSubmitting.value = false;
  }
};
</script>