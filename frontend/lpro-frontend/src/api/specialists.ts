import { apiClient } from "./client";
import type { Service, Specialist } from "../types/models";

export interface SpecialistCreatePayload {
  first_name: string;
  last_name: string;
  work_experience: string;
  photo: string;
}

export interface SpecialistUpdatePayload {
  first_name?: string;
  last_name?: string;
  work_experience?: string;
  photo?: string;
}

export interface AttachServicePayload {
  specialist_id: number;
  service_id: number;
}

export const getSpecialists = () => {
  return apiClient.get<Specialist[]>("/api/specialists");
};

export const getSpecialist = (specialistId: number | string) => {
  return apiClient.get<Specialist>(`/api/specialists/${specialistId}`);
};

export const createSpecialist = (payload: SpecialistCreatePayload) => {
  return apiClient.post<Specialist>("/api/specialists", payload);
};

export const updateSpecialist = (
  specialistId: number | string,
  payload: SpecialistUpdatePayload
) => {
  return apiClient.patch<Specialist>(`/api/specialists/${specialistId}`, payload);
};

export const getSpecialistServices = (specialistId: number | string) => {
  return apiClient.get<Service[]>(`/api/specialists/${specialistId}/services`);
};

export const attachServiceToSpecialist = (payload: AttachServicePayload) => {
  return apiClient.post(`/api/specialists/${payload.specialist_id}/services`, payload);
};