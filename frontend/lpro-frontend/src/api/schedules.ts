import { apiClient } from "./client";

export interface GenerateSchedulePayload {
  specialist_id: number;
  working_days: string[];
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  target_month: number;
  target_year: number;
}

export interface GenerateScheduleResponse {
  ok: boolean;
  action: string;
  processed_days: number;
}

export const generateSchedule = (payload: GenerateSchedulePayload) => {
  return apiClient.post<GenerateScheduleResponse>("/api/admin/schedules/generate", payload);
};