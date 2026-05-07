export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export const getTelegramInitData = (): string => {
  return window.Telegram?.WebApp?.initData || "";
};

export const authHeaders = () => ({
  "X-Telegram-Init-Data": getTelegramInitData(),
});

export const jsonHeaders = () => ({
  "Content-Type": "application/json",
  ...authHeaders(),
});

export async function request<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, options);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || "Ошибка запроса");
  }

  return await response.json();
}