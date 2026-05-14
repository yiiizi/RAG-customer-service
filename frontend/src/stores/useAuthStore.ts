/**
 * Authentication state management store.
 */

import { create } from 'zustand';
import type { UserResponse } from '@/types/auth';
import * as authService from '@/services/authService';
import { removeTokens } from '@/utils/token';
import { useChatStore } from '@/stores/useChatStore';

interface AuthState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  
  // Actions
  login: (data: authService.LoginRequest) => Promise<void>;
  register: (data: authService.RegisterRequest) => Promise<void>;
  logout: () => void;
  getCurrentUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()((
  set,
  get
) => ({
  user: null,
  isAuthenticated: false,
  loading: false,
  error: null,
  
  login: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await authService.login(data);
      useChatStore.getState().reset();
      set({
        user: response.user,
        isAuthenticated: true,
        loading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || '登录失败',
        loading: false,
      });
      throw error;
    }
  },
  
  register: async (data) => {
    set({ loading: true, error: null });
    try {
      const response = await authService.register(data);
      useChatStore.getState().reset();
      set({
        user: response.user,
        isAuthenticated: true,
        loading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || '注册失败',
        loading: false,
      });
      throw error;
    }
  },
  
  logout: () => {
    authService.logout();
    useChatStore.getState().reset();
    set({
      user: null,
      isAuthenticated: false,
      error: null,
    });
  },
  
  getCurrentUser: async () => {
    set({ loading: true, error: null });
    try {
      const user = await authService.getCurrentUser();
      set({
        user,
        isAuthenticated: true,
        loading: false,
      });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || '获取用户信息失败',
        loading: false,
      });
      throw error;
    }
  },
  
  clearError: () => {
    set({ error: null });
  },
}));
