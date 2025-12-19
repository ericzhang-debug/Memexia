/**
 * Authentication API service
 */

import { apiClient } from './client';
import type { Token, User, UserCreate, PasswordResetRequest, PasswordResetConfirm } from './types';

export const authApi = {
	/**
	 * Login with username and password (OAuth2 form)
	 */
	async login(username: string, password: string): Promise<Token> {
		const formData = new FormData();
		formData.append('username', username);
		formData.append('password', password);
		return apiClient.postForm<Token>('/api/v1/auth/token', formData);
	},

	/**
	 * Register a new user
	 */
	async register(data: UserCreate): Promise<User> {
		return apiClient.post<User>('/api/v1/auth/register', data, false);
	},

	/**
	 * Verify email with token
	 */
	async verifyEmail(token: string): Promise<{ message: string }> {
		return apiClient.post<{ message: string }>(`/api/v1/auth/verify-email?token=${token}`, undefined, false);
	},

	/**
	 * Request password reset
	 */
	async forgotPassword(data: PasswordResetRequest): Promise<{ message: string }> {
		return apiClient.post<{ message: string }>('/api/v1/auth/forgot-password', data, false);
	},

	/**
	 * Reset password with token
	 */
	async resetPassword(data: PasswordResetConfirm): Promise<{ message: string }> {
		return apiClient.post<{ message: string }>('/api/v1/auth/reset-password', data, false);
	},

	/**
	 * Get current logged in user
	 */
	async getCurrentUser(): Promise<User> {
		return apiClient.get<User>('/api/v1/users/me');
	}
};
