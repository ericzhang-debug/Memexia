<script lang="ts">
	import type { Snippet } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { isAdmin, user } from '$lib/stores';

	interface Props {
		children?: Snippet;
	}

	let { children }: Props = $props();

	// Redirect non-admins
	$effect(() => {
		if ($user && !$isAdmin) {
			goto('/app/dashboard');
		}
	});

	const navItems = [
		{ href: '/admin', label: 'Overview', icon: '📊', exact: true },
		{ href: '/admin/users', label: 'Users', icon: '👥' },
		{ href: '/admin/settings', label: 'Settings', icon: '⚙️' }
	];

	function isActive(href: string, exact: boolean = false): boolean {
		if (exact) {
			return $page.url.pathname === href;
		}
		return $page.url.pathname.startsWith(href);
	}
</script>

{#if $isAdmin}
	<div class="min-h-screen flex">
		<!-- Sidebar -->
		<aside class="w-64 bg-gray-800/50 border-r border-gray-700 flex flex-col">
			<!-- Header -->
			<div class="p-6 border-b border-gray-700">
				<a href="/app/dashboard" class="text-xl font-bold text-cyan-400">
					Memexia
				</a>
				<p class="text-xs text-gray-400 mt-1">Administration</p>
			</div>

			<!-- Navigation -->
			<nav class="flex-1 p-4">
				<ul class="space-y-1">
					{#each navItems as item}
						<li>
							<a
								href={item.href}
								class="flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors
									{isActive(item.href, item.exact)
									? 'bg-cyan-500/20 text-cyan-400'
									: 'text-gray-400 hover:bg-gray-700/50 hover:text-gray-200'}"
							>
								<span>{item.icon}</span>
								{item.label}
							</a>
						</li>
					{/each}
				</ul>
			</nav>

			<!-- Back to App -->
			<div class="p-4 border-t border-gray-700">
				<a
					href="/dashboard"
					class="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
				>
					← Back to App
				</a>
			</div>
		</aside>

		<!-- Main Content -->
		<main class="flex-1 overflow-auto">
			<div class="p-8">
				{@render children?.()}
			</div>
		</main>
	</div>
{/if}
