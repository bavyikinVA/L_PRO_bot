import { apiClient } from "./client";
import type { Service } from "../types/models";

export interface ServiceCreatePayload {
  label: string;
  description: string;
  price: number;
  duration_minutes: number;
}

export interface ServiceUpdatePayload {
  label?: string;
  description?: string;
  price?: number;
  duration_minutes?: number;
}

export const getServices = () => {
  return apiClient.get<Service[]>("/api/services");
};

export const getService = (serviceId: number | string) => {
  return apiClient.get<Service>(`/api/services/${serviceId}`);
};

export const createService = (payload: ServiceCreatePayload) => {
  return apiClient.post<Service>("/api/services", payload);
};

export const updateService = (
  serviceId: number | string,
  payload: ServiceUpdatePayload
) => {
  return apiClient.patch<Service>(`/api/services/${serviceId}`, payload);
};