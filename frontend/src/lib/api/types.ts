/**
 * Type definitions for API responses and requests
 */

// User types
export interface User {
	id: number;
	email: string;
	username: string;
	role: string;
	is_superuser: boolean;
	is_active: boolean;
	is_verified: boolean;
	created_at: string;
}

export interface UserCreate {
	email: string;
	username: string;
	password: string;
}

export interface UserRoleUpdate {
	role: 'guest' | 'user' | 'admin';
}

// Auth types
export interface Token {
	access_token: string;
	token_type: string;
	expires_at: string;
}

export interface LoginForm {
	username: string;
	password: string;
}

export interface PasswordResetRequest {
	email?: string;
}

export interface PasswordResetConfirm {
	token: string;
	new_password: string;
}

// Knowledge Base types
export interface KnowledgeBase {
	id: string;
	name: string;
	description: string | null;
	owner_id: number;
	seed_node_id: string | null;
	is_public: boolean;
	created_at: string;
	updated_at: string;
}

export interface KnowledgeBaseListItem {
	id: string;
	name: string;
	description: string | null;
	owner_id: number;
	is_public: boolean;
	created_at: string;
}

export interface KnowledgeBaseCreate {
	name: string;
	description?: string;
	is_public?: boolean;
	seed_content?: string;
}

export interface KnowledgeBaseUpdate {
	name?: string;
	description?: string;
	is_public?: boolean;
}

export interface KnowledgeBaseCopy {
	new_name?: string;
}

export interface PaginatedKnowledgeBases {
	items: KnowledgeBaseListItem[];
	total: number;
	page: number;
	page_size: number;
	total_pages: number;
}

// Node types
export interface Node {
	id: string;
	content: string;
	node_type: string;
	created_at: string;
	updated_at: string | null;
}

export interface NodeCreate {
	content: string;
	node_type?: string;
}

export interface NodeUpdate {
	content?: string;
	node_type?: string;
}

export interface AIExpandRequest {
	instruction?: string;
}

// Edge types
export interface Edge {
	id: string;
	source_id: string;
	target_id: string;
	relation_type: string;
	weight: number;
}

// Graph types
export interface GraphData {
	nodes: Node[];
	edges: Edge[];
}

// Admin settings types
export interface AuthSettings {
	enable_email: boolean;
	enable_phone: boolean;
	enable_qq: boolean;
}

export interface GraphDBSettings {
	db_type: 'kuzu' | 'nebula';
	kuzu_db_path: string;
	nebula_host: string;
	nebula_port: number;
	nebula_user: string;
	nebula_password: string;
}

// SSE Event types for streaming
export type StreamingNodeEventType =
	| 'start'
	| 'thinking'
	| 'chunk'
	| 'parsing'
	| 'node_created'
	| 'complete'
	| 'error';

export interface StreamingStartEvent {
	type: 'start';
	source_node: { id: string; content: string };
}

export interface StreamingThinkingEvent {
	type: 'thinking';
	message: string;
}

export interface StreamingChunkEvent {
	type: 'chunk';
	content: string;
}

export interface StreamingParsingEvent {
	type: 'parsing';
	message: string;
}

export interface StreamingNodeCreatedEvent {
	type: 'node_created';
	node: { id: string; content: string; node_type: string };
	relation: string;
}

export interface StreamingCompleteEvent {
	type: 'complete';
	total_nodes: number;
}

export interface StreamingErrorEvent {
	type: 'error';
	message: string;
}

export type StreamingNodeEvent =
	| StreamingStartEvent
	| StreamingThinkingEvent
	| StreamingChunkEvent
	| StreamingParsingEvent
	| StreamingNodeCreatedEvent
	| StreamingCompleteEvent
	| StreamingErrorEvent;

