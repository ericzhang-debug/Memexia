<script lang="ts">
	import type { HTMLTextareaAttributes } from 'svelte/elements';

	interface Props extends HTMLTextareaAttributes {
		label?: string;
		error?: string;
		class?: string;
		value?: string;
	}

	let {
		label,
		error,
		class: className = '',
		id,
		value = $bindable(''),
		...rest
	}: Props = $props();

	const textareaId = id || `textarea-${Math.random().toString(36).slice(2, 9)}`;
</script>

<div class="w-full {className}">
	{#if label}
		<label for={textareaId} class="block text-sm font-medium text-gray-300 mb-1.5">
			{label}
		</label>
	{/if}
	<textarea
		id={textareaId}
		class="w-full px-4 py-2.5 bg-gray-800 border rounded-lg text-gray-100 placeholder-gray-500
			focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent
			transition-all duration-200 resize-y min-h-[100px]
			{error ? 'border-red-500' : 'border-gray-600 hover:border-gray-500'}"
		bind:value
		{...rest}
	></textarea>
	{#if error}
		<p class="mt-1.5 text-sm text-red-400">{error}</p>
	{/if}
</div>
