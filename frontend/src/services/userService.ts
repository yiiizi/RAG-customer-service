/**
 * User management API service (admin only).
 */

import request from './request';
import type { UserResponse } from '@/types/auth';

export interface UserListResponse {
  items: UserResponse[];
  total: number;
}

/**
 * Get paginated list of all users (admin only).
 */
export const getUsers = async (
  page: number = 1,
  pageSize: number = 20
): Promise<UserListResponse> => {
  const response = await request.get('/admin/users', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

/**
 * Get a single user by ID (admin only).
 */
export const getUser = async (
  userId: number
): Promise<UserResponse> => {
  const response = await request.get(`/admin/users/${userId}`);
  return response.data;
};

/**
 * Update a user's role (admin only).
 */
export const updateUserRole = async (
  userId: number,
  newRole: string
): Promise<void> => {
  await request.put(`/admin/users/${userId}/role`, null, {
    params: { new_role: newRole },
  });
};

/**
 * Activate a user (admin only).
 */
export const activateUser = async (
  userId: number
): Promise<void> => {
  await request.put(`/admin/users/${userId}/activate`);
};

/**
 * Deactivate a user (admin only).
 */
export const deactivateUser = async (
  userId: number
): Promise<void> => {
  await request.put(`/admin/users/${userId}/deactivate`);
};

/**
 * Delete a user (admin only).
 */
export const deleteUser = async (
  userId: number
): Promise<void> => {
  await request.delete(`/admin/users/${userId}`);
};
