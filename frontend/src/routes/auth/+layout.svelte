<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		children?: Snippet;
	}

	let { children }: Props = $props();
</script>

<div class="min-h-screen flex items-center justify-center p-4">
	<div class="w-full max-w-md">
		<!-- Logo -->
		<div class="text-center mb-8">
			<h1 class="text-3xl font-bold text-cyan-400">Memexia</h1>
			<p class="text-gray-400 mt-2">Autonomous Thought Universe</p>
		</div>

		<!-- Content -->
		{@render children?.()}

		<!-- Footer -->
		<p class="text-center text-gray-500 text-sm mt-8">
			&copy; 2024 Memexia. Licensed under AGPL v3.
		</p>
	</div>
</div>
