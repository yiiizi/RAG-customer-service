import { create } from 'zustand';
import type { SettingsData } from '@/types/dashboard';
import * as api from '@/services/dashboardService';

const SAVE_TIMEOUT_MS = 15_000;

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
    } catch {
      // Error handled by axios interceptor
    } finally {
      set({ loading: false });
    }
  },

  save: async (data) => {
    set({ saving: true });
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), SAVE_TIMEOUT_MS);
    try {
      await api.updateSettings(data, controller.signal);
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        const timeoutErr = new Error('保存超时，服务器未响应，请稍后重试');
        throw timeoutErr;
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
      set({ saving: false });
    }
  },
}));
