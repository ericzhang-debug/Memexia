<script lang="ts">
	import { onMount } from 'svelte';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { Toast } from '$lib/components/ui';
	import { authActions, authLoading } from '$lib/stores';

	let { children } = $props();

	onMount(() => {
		// Initialize auth state from stored token
		authActions.init();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Memexia - Autonomous Thought Universe</title>
</svelte:head>

<Toast />

{#if $authLoading}
	<div class="fixed inset-0 flex items-center justify-center bg-gray-900">
		<div class="text-center">
			<div class="animate-spin w-12 h-12 border-4 border-gray-600 border-t-cyan-400 rounded-full mb-4"></div>
			<p class="text-gray-400 text-sm">Loading...</p>
		</div>
	</div>
{:else}
	{@render children()}
{/if}
