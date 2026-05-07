import { apiClient } from "./client";
import type { SlotsResponse, User } from "../types/models";

export interface BookingCreatePayload {
  specialist_id: number;
  user_id: number;
  service_id: number;
  booking_datetime: string;
  status: string;
  duration_minutes: number;
  is_cancelled: boolean;
}

export const getAdminUsers = () => {
  return apiClient.get<User[]>("/api/admin/users");
};

export const getAvailableSlots = (
  specialistId: number,
  startDate: string,
  serviceId: number
) => {
  return apiClient.get<SlotsResponse>(
    `/api/specialists/${specialistId}/slots?start_date=${startDate}&service_id=${serviceId}`
  );
};

export const createBooking = (payload: BookingCreatePayload) => {
  return apiClient.post("/api/bookings", payload);
};