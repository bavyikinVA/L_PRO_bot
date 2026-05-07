export interface User {
  id: number;
  telegram_id?: number | null;
  username?: string | null;
  first_name: string;
  last_name?: string | null;
  patronymic?: string | null;
  phone_number?: string | null;
  is_admin?: boolean;
}

export interface Service {
  id: number;
  label: string;
  description?: string;
  price: number;
  duration_minutes: number;
  icon?: string | null;
}

export interface Specialist {
  id: number;
  first_name: string;
  last_name: string;
  work_experience?: string | null;
  photo?: string | null;
}

export interface SlotsDay {
  day: string;
  date: string;
  slots: string[];
  total_slots: number;
}

export interface SlotsResponse {
  days: SlotsDay[];
  total_week_slots: number;
}