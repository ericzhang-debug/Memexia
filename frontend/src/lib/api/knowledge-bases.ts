/**
 * Knowledge Bases API service
 */

import { apiClient } from './client';
import type {
	KnowledgeBase,
	KnowledgeBaseCreate,
	KnowledgeBaseUpdate,
	KnowledgeBaseCopy,
	PaginatedKnowledgeBases
} from './types';

export const knowledgeBasesApi = {
	/**
	 * List knowledge bases with pagination
	 */
	async list(
		page: number = 1,
		pageSize: number = 20,
		mineOnly: boolean = false
	): Promise<PaginatedKnowledgeBases> {
		const params = new URLSearchParams({
			page: page.toString(),
			page_size: pageSize.toString(),
			mine_only: mineOnly.toString()
		});
		return apiClient.get<PaginatedKnowledgeBases>(`/api/v1/knowledge-bases?${params}`);
	},

	/**
	 * List only my knowledge bases
	 */
	async listMine(page: number = 1, pageSize: number = 20): Promise<PaginatedKnowledgeBases> {
		const params = new URLSearchParams({
			page: page.toString(),
			page_size: pageSize.toString()
		});
		return apiClient.get<PaginatedKnowledgeBases>(`/api/v1/knowledge-bases/my?${params}`);
	},

	/**
	 * Get a specific knowledge base
	 */
	async get(kbId: string): Promise<KnowledgeBase> {
		return apiClient.get<KnowledgeBase>(`/api/v1/knowledge-bases/${kbId}`);
	},

	/**
	 * Create a new knowledge base
	 */
	async create(data: KnowledgeBaseCreate): Promise<KnowledgeBase> {
		return apiClient.post<KnowledgeBase>('/api/v1/knowledge-bases', data);
	},

	/**
	 * Update a knowledge base
	 */
	async update(kbId: string, data: KnowledgeBaseUpdate): Promise<KnowledgeBase> {
		return apiClient.put<KnowledgeBase>(`/api/v1/knowledge-bases/${kbId}`, data);
	},

	/**
	 * Delete a knowledge base
	 */
	async delete(kbId: string): Promise<void> {
		return apiClient.delete<void>(`/api/v1/knowledge-bases/${kbId}`);
	},

	/**
	 * Copy a public knowledge base
	 */
	async copy(kbId: string, data: KnowledgeBaseCopy): Promise<KnowledgeBase> {
		return apiClient.post<KnowledgeBase>(`/api/v1/knowledge-bases/${kbId}/copy`, data);
	}
};
