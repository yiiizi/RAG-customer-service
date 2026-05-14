import { create } from 'zustand';
import type { DashboardStats } from '@/types/dashboard';
import { getDashboardStats, type DashboardRange } from '@/services/dashboardService';

interface DashboardState {
  stats: DashboardStats | null;
  loading: boolean;
  range: DashboardRange;
  setRange: (range: DashboardRange) => void;
  fetch: (range?: DashboardRange) => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  stats: null,
  loading: false,
  range: '7d',
  setRange: (range) => set({ range }),
  fetch: async (range) => {
    const selectedRange = range ?? get().range;
    set({ loading: true });
    try {
      const stats = await getDashboardStats(selectedRange);
      set({ stats, range: selectedRange, loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));
