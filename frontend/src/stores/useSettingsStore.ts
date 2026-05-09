import { create } from 'zustand';
import type { SettingsData } from '@/types/dashboard';
import * as api from '@/services/dashboardService';

interface SettingsState {
  settings: SettingsData | null;
  loading: boolean;
  saving: boolean;
  fetch: () => Promise<void>;
  save: (data: Record<string, unknown>) => Promise<void>;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: null,
  loading: false,
  saving: false,

  fetch: async () => {
    set({ loading: true });
    try {
      const settings = await api.getSettings();
      set({ settings });
    } finally {
      set({ loading: false });
    }
  },

  save: async (data) => {
    set({ saving: true });
    try {
      await api.updateSettings(data);
    } finally {
      set({ saving: false });
    }
  },
}));
