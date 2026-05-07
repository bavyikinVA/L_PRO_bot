import { ref } from "vue";
import type { User } from "../types/models";
import { getAdminUsers } from "../api/adminBookings";

export function useAdminUsers() {
  const users = ref<User[]>([]);
  const isLoading = ref(false);
  const errorMessage = ref("");

  const loadUsers = async () => {
    isLoading.value = true;
    errorMessage.value = "";

    try {
      users.value = await getAdminUsers();
    } catch (error) {
      console.error(error);
      errorMessage.value = "Не удалось загрузить клиентов";
    } finally {
      isLoading.value = false;
    }
  };

  return {
    users,
    isLoading,
    errorMessage,
    loadUsers,
  };
}