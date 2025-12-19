/**
 * HTTP client for API communication with JWT authentication support
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

export interface ApiError {
	status: number;
	message: string;
	detail?: string;
}

export class ApiClient {
	private baseUrl: string;

	constructor(baseUrl: string = API_BASE_URL) {
		this.baseUrl = baseUrl;
	}

	private getToken(): string | null {
		if (typeof window === 'undefined') return null;
		return localStorage.getItem('access_token');
	}

	private getHeaders(includeAuth: boolean = true): Headers {
		const headers = new Headers({
			'Content-Type': 'application/json'
		});

		if (includeAuth) {
			const token = this.getToken();
			if (token) {
				headers.set('Authorization', `Bearer ${token}`);
			}
		}

		return headers;
	}

	private async handleResponse<T>(response: Response): Promise<T> {
		if (!response.ok) {
			let errorMessage = `HTTP error! status: ${response.status}`;
			let detail: string | undefined;

			try {
				const errorData = await response.json();
				errorMessage = errorData.detail || errorData.message || errorMessage;
				detail = errorData.detail;
			} catch {
				// Failed to parse error response
			}

			// Handle 401 Unauthorized - redirect to login
			if (response.status === 401) {
				if (typeof window !== 'undefined') {
					localStorage.removeItem('access_token');
					localStorage.removeItem('token_expires_at');
					// Only redirect if not already on auth pages
					if (!window.location.pathname.startsWith('/login') &&
						!window.location.pathname.startsWith('/register')) {
						window.location.href = '/login';
					}
				}
			}

			const error: ApiError = {
				status: response.status,
				message: errorMessage,
				detail
			};
			throw error;
		}

		// Handle empty responses (204 No Content)
		if (response.status === 204) {
			return undefined as T;
		}

		return response.json();
	}

	async get<T>(endpoint: string, includeAuth: boolean = true): Promise<T> {
		const response = await fetch(`${this.baseUrl}${endpoint}`, {
			method: 'GET',
			headers: this.getHeaders(includeAuth)
		});
		return this.handleResponse<T>(response);
	}

	async post<T>(endpoint: string, data?: unknown, includeAuth: boolean = true): Promise<T> {
		const response = await fetch(`${this.baseUrl}${endpoint}`, {
			method: 'POST',
			headers: this.getHeaders(includeAuth),
			body: data ? JSON.stringify(data) : undefined
		});
		return this.handleResponse<T>(response);
	}

	async postForm<T>(endpoint: string, formData: FormData): Promise<T> {
		const headers = new Headers();
		const token = this.getToken();
		if (token) {
			headers.set('Authorization', `Bearer ${token}`);
		}

		const response = await fetch(`${this.baseUrl}${endpoint}`, {
			method: 'POST',
			headers,
			body: formData
		});
		return this.handleResponse<T>(response);
	}

	async put<T>(endpoint: string, data?: unknown, includeAuth: boolean = true): Promise<T> {
		const response = await fetch(`${this.baseUrl}${endpoint}`, {
			method: 'PUT',
			headers: this.getHeaders(includeAuth),
			body: data ? JSON.stringify(data) : undefined
		});
		return this.handleResponse<T>(response);
	}

	async patch<T>(endpoint: string, data?: unknown, includeAuth: boolean = true): Promise<T> {
		const response = await fetch(`${this.baseUrl}${endpoint}`, {
			method: 'PATCH',
			headers: this.getHeaders(includeAuth),
			body: data ? JSON.stringify(data) : undefined
		});
		return this.handleResponse<T>(response);
	}

	async delete<T>(endpoint: string, includeAuth: boolean = true): Promise<T> {
		const response = await fetch(`${this.baseUrl}${endpoint}`, {
			method: 'DELETE',
			headers: this.getHeaders(includeAuth)
		});
		return this.handleResponse<T>(response);
	}

	/**
	 * SSE (Server-Sent Events) streaming request
	 */
	async *stream<T>(
		endpoint: string,
		data?: unknown,
		signal?: AbortSignal
	): AsyncGenerator<T, void, unknown> {
		const response = await fetch(`${this.baseUrl}${endpoint}`, {
			method: 'POST',
			headers: this.getHeaders(true),
			body: data ? JSON.stringify(data) : undefined,
			signal
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const reader = response.body?.getReader();
		if (!reader) {
			throw new Error('No response body');
		}

		const decoder = new TextDecoder();
		let buffer = '';

		try {
			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split('\n');
				buffer = lines.pop() || '';

				for (const line of lines) {
					if (line.startsWith('data: ')) {
						const data = line.slice(6);
						if (data === '[DONE]') {
							return;
						}
						try {
							yield JSON.parse(data) as T;
						} catch {
							// Skip non-JSON data
						}
					}
				}
			}
		} finally {
			reader.releaseLock();
		}
	}
}

export const apiClient = new ApiClient();
