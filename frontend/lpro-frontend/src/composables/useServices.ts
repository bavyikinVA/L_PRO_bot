import { ref } from "vue";
import type { Service } from "../types/models";
import { getServices } from "../api/services";

export function useServices() {
  const services = ref<Service[]>([]);
  const isLoading = ref(false);
  const errorMessage = ref("");

  const loadServices = async () => {
    isLoading.value = true;
    errorMessage.value = "";

    try {
      services.value = await getServices();
    } catch (error) {
      console.error(error);
      errorMessage.value = "Не удалось загрузить услуги";
    } finally {
      isLoading.value = false;
    }
  };

  return {
    services,
    isLoading,
    errorMessage,
    loadServices,
  };
}