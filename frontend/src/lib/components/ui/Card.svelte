<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		class?: string;
		padding?: 'sm' | 'md' | 'lg';
		children?: Snippet;
	}

	let { class: className = '', padding = 'md', children }: Props = $props();

	const paddingClasses = {
		sm: 'p-4',
		md: 'p-6',
		lg: 'p-8'
	};
</script>

<div
	class="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-xl shadow-lg {paddingClasses[padding]} {className}"
>
	{@render children?.()}
</div>
