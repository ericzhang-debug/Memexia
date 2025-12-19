/**
 * Admin API service
 */

import { apiClient } from './client';
import type { AuthSettings, GraphDBSettings } from './types';

export const adminApi = {
	/**
	 * Get authentication settings
	 */
	async getAuthSettings(): Promise<AuthSettings> {
		return apiClient.get<AuthSettings>('/api/v1/admin/settings/auth');
	},

	/**
	 * Update authentication settings
	 */
	async updateAuthSettings(data: AuthSettings): Promise<AuthSettings> {
		return apiClient.put<AuthSettings>('/api/v1/admin/settings/auth', data);
	},

	/**
	 * Get graph database settings
	 */
	async getGraphDBSettings(): Promise<GraphDBSettings> {
		return apiClient.get<GraphDBSettings>('/api/v1/admin/settings/graph-db');
	},

	/**
	 * Update graph database settings
	 */
	async updateGraphDBSettings(data: GraphDBSettings): Promise<GraphDBSettings> {
		return apiClient.put<GraphDBSettings>('/api/v1/admin/settings/graph-db', data);
	}
};
