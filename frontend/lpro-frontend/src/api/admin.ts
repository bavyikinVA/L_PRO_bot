const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export function getTelegramInitData(): string {
  return window.Telegram?.WebApp?.initData || "";
}

export async function checkAdminAccess() {
  const initData = getTelegramInitData();

  const response = await fetch(`${API_BASE_URL}/admin/me`, {
    method: "GET",
    headers: {
      "X-Telegram-Init-Data": initData,
    },
  });

  if (!response.ok) {
    throw new Error("Нет доступа к админ-панели");
  }

  return await response.json();
}