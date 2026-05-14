import request from './request';
import type { DashboardStats, SettingsData } from '@/types/dashboard';

export type DashboardRange = 'today' | '7d' | '30d';

export async function getDashboardStats(range: DashboardRange = '7d'): Promise<DashboardStats> {
  const res = await request.get<DashboardStats>('/dashboard', { params: { range } });
  return res.data;
}

export async function getSettings(): Promise<SettingsData> {
  const res = await request.get<SettingsData>('/settings');
  return res.data;
}

export async function updateSettings(data: Record<string, unknown>, signal?: AbortSignal): Promise<void> {
  await request.put('/settings', data, { signal });
}
