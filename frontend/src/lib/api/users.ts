/**
 * Users API service (admin endpoints)
 */

import { apiClient } from './client';
import type { User, UserRoleUpdate } from './types';

export const usersApi = {
	/**
	 * List all users (admin only)
	 */
	async list(skip: number = 0, limit: number = 100): Promise<User[]> {
		return apiClient.get<User[]>(`/api/v1/users?skip=${skip}&limit=${limit}`);
	},

	/**
	 * Get a specific user by ID
	 */
	async get(userId: number): Promise<User> {
		return apiClient.get<User>(`/api/v1/users/${userId}`);
	},

	/**
	 * Update user role
	 */
	async updateRole(userId: number, data: UserRoleUpdate): Promise<User> {
		return apiClient.patch<User>(`/api/v1/users/${userId}/role`, data);
	},

	/**
	 * Delete a user
	 */
	async delete(userId: number): Promise<void> {
		return apiClient.delete<void>(`/api/v1/users/${userId}`);
	},

	/**
	 * Activate a user
	 */
	async activate(userId: number): Promise<User> {
		return apiClient.patch<User>(`/api/v1/users/${userId}/activate`);
	},

	/**
	 * Deactivate a user
	 */
	async deactivate(userId: number): Promise<User> {
		return apiClient.patch<User>(`/api/v1/users/${userId}/deactivate`);
	}
};
