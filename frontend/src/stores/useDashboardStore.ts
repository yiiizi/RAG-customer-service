import { create } from 'zustand';
import type { DashboardStats } from '@/types/dashboard';
import { getDashboardStats } from '@/services/dashboardService';

interface DashboardState {
  stats: DashboardStats | null;
  loading: boolean;
  fetch: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  loading: false,
  fetch: async () => {
    set({ loading: true });
    try {
      const stats = await getDashboardStats();
      set({ stats, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));
