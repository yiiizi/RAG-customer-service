/**
 * Authentication API service.
 */

import request from './request';
import { saveTokens, removeTokens } from '@/utils/token';

export interface LoginRequest {
  login_type: string;
  username?: string;
  email?: string;
  phone?: string;
  password: string;
  verification_code?: string;
}

export interface RegisterRequest {
  username: string;
  email?: string;
  phone?: string;
  password: string;
  confirm_password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: number;
    username?: string;
    email?: string;
    phone?: string;
    role: string;
    is_active: boolean;
    created_at?: string;
  };
}

export interface UserResponse {
  id: number;
  username?: string;
  email?: string;
  phone?: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

/**
 * Login user.
 */
export const login = async (data: LoginRequest): Promise<AuthResponse> => {
  const response = await request.post('/auth/login', data);
  
  // Save tokens
  saveTokens(response.data.access_token, response.data.refresh_token);
  
  return response.data;
};

/**
 * Register user.
 */
export const register = async (data: RegisterRequest): Promise<AuthResponse> => {
  const response = await request.post('/auth/register', data);
  
  // Save tokens
  saveTokens(response.data.access_token, response.data.refresh_token);
  
  return response.data;
};

/**
 * Refresh access token.
 */
export const refreshToken = async (refreshToken: string): Promise<{ access_token: string; token_type: string; expires_in: number }> => {
  const response = await request.post('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
};

/**
 * Get current user info.
 */
export const getCurrentUser = async (): Promise<UserResponse> => {
  const response = await request.get('/auth/me');
  return response.data;
};

/**
 * Logout user.
 */
export const logout = (): void => {
  removeTokens();
};

/**
 * Check if user is logged in.
 */
export const isLoggedIn = (): boolean => {
  const token = localStorage.getItem('rag_access_token');
  return !!token;
};
