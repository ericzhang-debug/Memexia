<script lang="ts">
	import type { Snippet } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { isAuthenticated, isAdmin, user, authActions } from '$lib/stores';
	import { toast } from '$lib/stores/toast';

	interface Props {
		children?: Snippet;
	}

	let { children }: Props = $props();
	let menuOpen = $state(false);

	// Redirect to login if not authenticated
	$effect(() => {
		if (!$isAuthenticated) {
			goto('/auth/login');
		}
	});

	function handleLogout() {
		authActions.logout();
		toast.success('Logged out successfully');
		goto('/auth/login');
	}

	const navItems = [
		{ href: '/app/dashboard', label: 'Dashboard', icon: '🏠' },
		{ href: '/app/knowledge-bases', label: 'Knowledge Bases', icon: '📚' }
	];
</script>

{#if $isAuthenticated}
	<div class="min-h-screen flex flex-col">
		<!-- Top Navigation -->
		<nav class="bg-gray-800/80 backdrop-blur-sm border-b border-gray-700 sticky top-0 z-40">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div class="flex items-center justify-between h-16">
					<!-- Logo & Nav -->
					<div class="flex items-center gap-8">
						<a href="/app/dashboard" class="text-xl font-bold text-cyan-400">
							Memexia
						</a>

						<div class="hidden md:flex items-center gap-1">
							{#each navItems as item}
								<a
									href={item.href}
									class="px-4 py-2 rounded-lg text-sm font-medium transition-colors
										{$page.url.pathname.startsWith(item.href)
										? 'bg-gray-700 text-white'
										: 'text-gray-300 hover:bg-gray-700/50 hover:text-white'}"
								>
									<span class="mr-2">{item.icon}</span>
									{item.label}
								</a>
							{/each}

							{#if $isAdmin}
								<a
									href="/admin"
									class="px-4 py-2 rounded-lg text-sm font-medium transition-colors
										{$page.url.pathname.startsWith('/admin')
										? 'bg-gray-700 text-white'
										: 'text-gray-300 hover:bg-gray-700/50 hover:text-white'}"
								>
									<span class="mr-2">⚙️</span>
									Admin
								</a>
							{/if}
						</div>
					</div>

					<!-- User Menu -->
					<div class="relative">
						<button
							onclick={() => (menuOpen = !menuOpen)}
							class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-700/50 transition-colors"
						>
							<div class="w-8 h-8 bg-cyan-500/20 rounded-full flex items-center justify-center text-cyan-400 font-medium">
								{$user?.username?.charAt(0).toUpperCase() || '?'}
							</div>
							<span class="hidden sm:inline">{$user?.username}</span>
							<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
							</svg>
						</button>

						{#if menuOpen}
							<!-- svelte-ignore a11y_no_static_element_interactions -->
							<div
								class="fixed inset-0"
								onclick={() => (menuOpen = false)}
								onkeydown={(e) => e.key === 'Escape' && (menuOpen = false)}
							></div>
							<div class="absolute right-0 mt-2 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-lg py-1 z-50">
								<div class="px-4 py-2 border-b border-gray-700">
									<p class="text-sm font-medium text-gray-100">{$user?.username}</p>
									<p class="text-xs text-gray-400">{$user?.email}</p>
								</div>
								<a
									href="/profile"
									onclick={() => (menuOpen = false)}
									class="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-700"
								>
									Profile
								</a>
								<button
									onclick={handleLogout}
									class="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-gray-700"
								>
									Sign out
								</button>
							</div>
						{/if}
					</div>

					<!-- Mobile menu button -->
					<button class="md:hidden p-2 text-gray-400 hover:text-white" onclick={() => (menuOpen = !menuOpen)}>
						<svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
						</svg>
					</button>
				</div>
			</div>
		</nav>

		<!-- Main Content -->
		<main class="flex-1">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
				{@render children?.()}
			</div>
		</main>

		<!-- Footer -->
		<footer class="bg-gray-800/50 border-t border-gray-700 py-4">
			<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-gray-500">
				Memexia &copy; 2024 | Licensed under AGPL v3
			</div>
		</footer>
	</div>
{/if}
