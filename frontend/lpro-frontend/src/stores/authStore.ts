import { defineStore } from "pinia";
import { ref } from "vue";
import { apiClient } from "../api/client";

interface AdminMeResponse {
  ok: boolean;
  telegram_id: number;
  first_name?: string;
  username?: string;
}

export const useAuthStore = defineStore("auth", () => {
  const isLoading = ref(false);
  const isAdmin = ref(false);
  const isChecked = ref(false);
  const errorMessage = ref("");
  const admin = ref<AdminMeResponse | null>(null);

  const checkAdmin = async () => {
    if (isChecked.value) {
      return isAdmin.value;
    }

    isLoading.value = true;
    errorMessage.value = "";

    try {
      const result = await apiClient.get<AdminMeResponse>("/api/admin/me");

      admin.value = result;
      isAdmin.value = true;
      isChecked.value = true;

      return true;
    } catch (error) {
      console.error(error);

      admin.value = null;
      isAdmin.value = false;
      isChecked.value = true;
      errorMessage.value = "У вас нет доступа к админ-панели";

      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const reset = () => {
    isLoading.value = false;
    isAdmin.value = false;
    isChecked.value = false;
    errorMessage.value = "";
    admin.value = null;
  };

  return {
    isLoading,
    isAdmin,
    isChecked,
    errorMessage,
    admin,
    checkAdmin,
    reset,
  };
});