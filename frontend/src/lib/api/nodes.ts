/**
 * Nodes API service
 */

import { apiClient } from './client';
import type { Node, NodeCreate, NodeUpdate, AIExpandRequest, GraphData, StreamingNodeEvent } from './types';

export const nodesApi = {
	/**
	 * Get all nodes and edges in a knowledge base (graph data)
	 */
	async getGraphData(kbId: string): Promise<GraphData> {
		return apiClient.get<GraphData>(`/api/v1/knowledge-bases/${kbId}/nodes/`);
	},

	/**
	 * Get a specific node
	 */
	async get(kbId: string, nodeId: string): Promise<Node> {
		return apiClient.get<Node>(`/api/v1/knowledge-bases/${kbId}/nodes/${nodeId}`);
	},

	/**
	 * Create a new node
	 */
	async create(kbId: string, data: NodeCreate): Promise<Node> {
		return apiClient.post<Node>(`/api/v1/knowledge-bases/${kbId}/nodes/`, data);
	},

	/**
	 * Update a node
	 */
	async update(kbId: string, nodeId: string, data: NodeUpdate): Promise<Node> {
		return apiClient.put<Node>(`/api/v1/knowledge-bases/${kbId}/nodes/${nodeId}`, data);
	},

	/**
	 * Delete a node
	 */
	async delete(kbId: string, nodeId: string): Promise<void> {
		return apiClient.delete<void>(`/api/v1/knowledge-bases/${kbId}/nodes/${nodeId}`);
	},

	/**
	 * Expand a node using AI (non-streaming, legacy)
	 */
	async expand(kbId: string, nodeId: string, data: AIExpandRequest): Promise<Node[]> {
		return apiClient.post<Node[]>(`/api/v1/knowledge-bases/${kbId}/nodes/${nodeId}/expand`, data);
	},

	/**
	 * Expand a node using AI with streaming response
	 */
	async *expandStream(
		kbId: string,
		nodeId: string,
		data: AIExpandRequest,
		signal?: AbortSignal
	): AsyncGenerator<StreamingNodeEvent, void, unknown> {
		yield* apiClient.stream<StreamingNodeEvent>(
			`/api/v1/knowledge-bases/${kbId}/nodes/${nodeId}/expand-stream`,
			data,
			signal
		);
	}
};
