<script lang="ts">
	/**
	 * Node Popup Component
	 *
	 * Displays node details and actions when a node is clicked in the graph.
	 */
	import type { Node } from '$lib/api';
	import { Button } from '$lib/components/ui';
	import { createEventDispatcher } from 'svelte';

	interface Props {
		node: Node | null;
		position: { x: number; y: number };
		isSeedNode?: boolean;
		canEdit?: boolean;
	}

	let { node, position, isSeedNode = false, canEdit = false }: Props = $props();

	const dispatch = createEventDispatcher<{
		close: void;
		edit: Node;
		delete: Node;
		expand: Node;
		createLinked: Node;
	}>();

	// Adjust position to keep popup in viewport
	let adjustedPosition = $derived({
		x: Math.min(position.x + 10, window.innerWidth - 320),
		y: Math.min(position.y + 10, window.innerHeight - 350)
	});
</script>

{#if node}
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-40"
		onclick={() => dispatch('close')}
		onkeydown={(e) => e.key === 'Escape' && dispatch('close')}
	></div>

	<!-- Popup -->
	<div
		class="fixed z-50 w-72 bg-gray-800/95 backdrop-blur-sm border border-gray-700 rounded-xl shadow-2xl"
		style="left: {adjustedPosition.x}px; top: {adjustedPosition.y}px;"
	>
		<!-- Header -->
		<div class="flex items-center justify-between px-4 py-3 border-b border-gray-700">
			<div class="flex items-center gap-2">
				<span class="px-2 py-0.5 text-xs bg-cyan-500/20 text-cyan-400 rounded">
					{node.node_type}
				</span>
				{#if isSeedNode}
					<span class="px-2 py-0.5 text-xs bg-yellow-500/20 text-yellow-400 rounded">
						Seed
					</span>
				{/if}
			</div>
			<button
				onclick={() => dispatch('close')}
				class="p-1 text-gray-400 hover:text-gray-200 transition-colors"
			>
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Content -->
		<div class="p-4">
			<p class="text-gray-100 text-sm leading-relaxed mb-4 max-h-32 overflow-y-auto">
				{node.content}
			</p>

			<div class="text-xs text-gray-500 space-y-1 mb-4">
				<p>ID: {node.id.slice(0, 8)}...</p>
				<p>Created: {new Date(node.created_at).toLocaleString()}</p>
				{#if node.updated_at}
					<p>Updated: {new Date(node.updated_at).toLocaleString()}</p>
				{/if}
			</div>
		</div>

		<!-- Actions -->
		{#if canEdit}
			<div class="px-4 pb-4 space-y-2">
				<Button
					class="w-full"
					onclick={() => dispatch('expand', node)}
				>
					<span class="mr-2">🧠</span>
					AI Expand
				</Button>

				<div class="grid grid-cols-2 gap-2">
					<Button
						variant="secondary"
						size="sm"
						onclick={() => dispatch('edit', node)}
					>
						Edit
					</Button>
					<Button
						variant="secondary"
						size="sm"
						onclick={() => dispatch('createLinked', node)}
					>
						+ Link
					</Button>
				</div>

				{#if !isSeedNode}
					<Button
						variant="danger"
						size="sm"
						class="w-full"
						onclick={() => dispatch('delete', node)}
					>
						Delete
					</Button>
				{/if}
			</div>
		{/if}
	</div>
{/if}
