/**
 * Authentication store for managing user session state
 */

import { writable, derived, get } from 'svelte/store';
import type { User } from '$lib/api/types';
import { authApi } from '$lib/api/auth';
import { browser } from '$app/environment';

// Token store with localStorage persistence
function createTokenStore() {
	const initialToken = browser ? localStorage.getItem('access_token') : null;
	const { subscribe, set, update } = writable<string | null>(initialToken);

	return {
		subscribe,
		set: (value: string | null) => {
			if (browser) {
				if (value) {
					localStorage.setItem('access_token', value);
				} else {
					localStorage.removeItem('access_token');
				}
			}
			set(value);
		},
		clear: () => {
			if (browser) {
				localStorage.removeItem('access_token');
				localStorage.removeItem('token_expires_at');
			}
			set(null);
		}
	};
}

// Token expiration store
function createExpiresAtStore() {
	const initialExpires = browser ? localStorage.getItem('token_expires_at') : null;
	const { subscribe, set } = writable<string | null>(initialExpires);

	return {
		subscribe,
		set: (value: string | null) => {
			if (browser) {
				if (value) {
					localStorage.setItem('token_expires_at', value);
				} else {
					localStorage.removeItem('token_expires_at');
				}
			}
			set(value);
		}
	};
}

// User info store
function createUserStore() {
	const { subscribe, set, update } = writable<User | null>(null);

	return {
		subscribe,
		set,
		update,
		clear: () => set(null)
	};
}

// Loading state store
function createLoadingStore() {
	const { subscribe, set } = writable<boolean>(true);
	return { subscribe, set };
}

// Create stores
export const token = createTokenStore();
export const tokenExpiresAt = createExpiresAtStore();
export const user = createUserStore();
export const authLoading = createLoadingStore();

// Derived stores
export const isAuthenticated = derived(
	[token, user],
	([$token, $user]) => !!$token && !!$user
);

export const isAdmin = derived(
	user,
	($user) => $user?.is_superuser || $user?.role === 'admin'
);

// Auth actions
export const authActions = {
	/**
	 * Initialize auth state from stored token
	 */
	async init() {
		authLoading.set(true);
		const currentToken = get(token);

		if (!currentToken) {
			authLoading.set(false);
			return;
		}

		// Check if token is expired
		const expiresAt = get(tokenExpiresAt);
		if (expiresAt) {
			const expiresDate = new Date(expiresAt);
			if (expiresDate < new Date()) {
				// Token expired, clear auth state
				token.clear();
				tokenExpiresAt.set(null);
				user.clear();
				authLoading.set(false);
				return;
			}
		}

		try {
			const currentUser = await authApi.getCurrentUser();
			user.set(currentUser);
		} catch (error) {
			// Token invalid, clear auth state
			token.clear();
			tokenExpiresAt.set(null);
			user.clear();
		} finally {
			authLoading.set(false);
		}
	},

	/**
	 * Login user
	 */
	async login(username: string, password: string) {
		const response = await authApi.login(username, password);
		token.set(response.access_token);
		tokenExpiresAt.set(response.expires_at);

		// Fetch user info
		const currentUser = await authApi.getCurrentUser();
		user.set(currentUser);

		return currentUser;
	},

	/**
	 * Logout user
	 */
	logout() {
		token.clear();
		tokenExpiresAt.set(null);
		user.clear();
	},

	/**
	 * Register new user
	 */
	async register(email: string, username: string, password: string) {
		return authApi.register({ email, username, password });
	}
};
