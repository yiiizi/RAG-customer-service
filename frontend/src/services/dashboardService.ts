import request from './request';
import type { DashboardStats, SettingsData } from '@/types/dashboard';

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await request.get<DashboardStats>('/dashboard');
  return res.data;
}

export async function getSettings(): Promise<SettingsData> {
  const res = await request.get<SettingsData>('/settings');
  return res.data;
}

export async function updateSettings(data: Record<string, unknown>): Promise<void> {
  await request.put('/settings', data);
}
