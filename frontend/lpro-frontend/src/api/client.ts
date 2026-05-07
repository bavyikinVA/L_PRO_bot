import { getTelegramInitData } from "./http";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

type RequestMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

interface ApiRequestOptions {
  method?: RequestMethod;
  body?: unknown;
  headers?: HeadersInit;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl = "") {
    this.baseUrl = baseUrl;
  }

  private getDefaultHeaders(): HeadersInit {
    return {
      "X-Telegram-Init-Data": getTelegramInitData(),
    };
  }

  private getJsonHeaders(): HeadersInit {
    return {
      ...this.getDefaultHeaders(),
      "Content-Type": "application/json",
    };
  }

  async request<T>(url: string, options: ApiRequestOptions = {}): Promise<T> {
    const method = options.method || "GET";

    const headers =
      options.body !== undefined
        ? {
            ...this.getJsonHeaders(),
            ...options.headers,
          }
        : {
            ...this.getDefaultHeaders(),
            ...options.headers,
          };

    const response = await fetch(`${this.baseUrl}${url}`, {
      method,
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || `Ошибка запроса: ${response.status}`);
    }

    if (response.status === 204) {
      return null as T;
    }

    return await response.json();
  }

  get<T>(url: string, options: Omit<ApiRequestOptions, "method" | "body"> = {}) {
    return this.request<T>(url, {
      ...options,
      method: "GET",
    });
  }

  post<T>(url: string, body?: unknown, options: Omit<ApiRequestOptions, "method" | "body"> = {}) {
    return this.request<T>(url, {
      ...options,
      method: "POST",
      body,
    });
  }

  patch<T>(url: string, body?: unknown, options: Omit<ApiRequestOptions, "method" | "body"> = {}) {
    return this.request<T>(url, {
      ...options,
      method: "PATCH",
      body,
    });
  }

  put<T>(url: string, body?: unknown, options: Omit<ApiRequestOptions, "method" | "body"> = {}) {
    return this.request<T>(url, {
      ...options,
      method: "PUT",
      body,
    });
  }

  delete<T>(url: string, options: Omit<ApiRequestOptions, "method" | "body"> = {}) {
    return this.request<T>(url, {
      ...options,
      method: "DELETE",
    });
  }
}

export const apiClient = new ApiClient(API_BASE_URL);