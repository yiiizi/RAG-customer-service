/**
 * Model configuration state management store.
 */

import { create } from 'zustand';
import type { ModelConfig } from '@/types/modelConfig';
import * as modelConfigService from '@/services/modelConfigService';

interface ModelConfigState {
  configs: ModelConfig[];
  loading: boolean;
  error: string | null;
  
  // Actions
  loadConfigs: () => Promise<void>;
  addConfig: (data: modelConfigService.ModelConfigCreateRequest) => Promise<void>;
  updateConfig: (id: number, data: modelConfigService.ModelConfigUpdateRequest) => Promise<void>;
  deleteConfig: (id: number) => Promise<void>;
  setDefaultConfig: (id: number) => Promise<void>;
  clearError: () => void;
}

export const useModelConfigStore = create<ModelConfigState>()((
  set,
  get
) => ({
  configs: [],
  loading: false,
  error: null,
  
  loadConfigs: async () => {
    set({ loading: true, error: null });
    try {
      const data = await modelConfigService.getModelConfigs();
      set({
        configs: data.items,
        loading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || '加载配置失败',
        loading: false,
      });
      throw error;
    }
  },
  
  addConfig: async (data) => {
    set({ loading: true, error: null });
    try {
      await modelConfigService.createModelConfig(data);
      // Reload configs
      await get().loadConfigs();
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || '添加配置失败',
        loading: false,
      });
      throw error;
    }
  },
  
  updateConfig: async (id, data) => {
    set({ loading: true, error: null });
    try {
      await modelConfigService.updateModelConfig(id, data);
      // Reload configs
      await get().loadConfigs();
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || '更新配置失败',
        loading: false,
      });
      throw error;
    }
  },
  
  deleteConfig: async (id) => {
    set({ loading: true, error: null });
    try {
      await modelConfigService.deleteModelConfig(id);
      // Reload configs
      await get().loadConfigs();
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || '删除配置失败',
        loading: false,
      });
      throw error;
    }
  },
  
  setDefaultConfig: async (id) => {
    set({ loading: true, error: null });
    try {
      await modelConfigService.setDefaultModelConfig(id);
      // Reload configs
      await get().loadConfigs();
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || '设置默认失败',
        loading: false,
      });
      throw error;
    }
  },
  
  clearError: () => {
    set({ error: null });
  },
}));
