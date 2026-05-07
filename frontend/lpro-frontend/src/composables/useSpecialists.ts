import { ref } from "vue";
import type { Specialist } from "../types/models";
import { getSpecialists } from "../api/specialists";

export function useSpecialists() {
  const specialists = ref<Specialist[]>([]);
  const isLoading = ref(false);
  const errorMessage = ref("");

  const loadSpecialists = async () => {
    isLoading.value = true;
    errorMessage.value = "";

    try {
      specialists.value = await getSpecialists();
    } catch (error) {
      console.error(error);
      errorMessage.value = "Не удалось загрузить мастеров";
    } finally {
      isLoading.value = false;
    }
  };

  return {
    specialists,
    isLoading,
    errorMessage,
    loadSpecialists,
  };
}