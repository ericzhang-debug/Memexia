<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	interface Props extends HTMLInputAttributes {
		label?: string;
		error?: string;
		class?: string;
		value?: string|number;
	}

	let {
		label,
		error,
		class: className = '',
		id,
		type = 'text',
		value = $bindable(''),
		...rest
	}: Props = $props();

	const inputId = id || `input-${Math.random().toString(36).slice(2, 9)}`;
</script>

<div class="w-full {className}">
	{#if label}
		<label for={inputId} class="block text-sm font-medium text-gray-300 mb-1.5">
			{label}
		</label>
	{/if}
	<input
		{id}
		{type}
		bind:value
		class="w-full px-4 py-2.5 bg-gray-800 border rounded-lg text-gray-100 placeholder-gray-500
			focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent
			transition-all duration-200
			{error ? 'border-red-500' : 'border-gray-600 hover:border-gray-500'}"
		{...rest}
	/>
	{#if error}
		<p class="mt-1.5 text-sm text-red-400">{error}</p>
	{/if}
</div>
