<script lang="ts">
	/**
	 * Create Node Dialog
	 *
	 * Dialog for manually creating a new node, optionally linked to another node.
	 */
	import type { Node } from '$lib/api';
	import { Dialog, Button, Textarea, Input } from '$lib/components/ui';
	import { createEventDispatcher } from 'svelte';

	interface Props {
		open: boolean;
		linkedNode?: Node | null;
		loading?: boolean;
	}

	let { open = $bindable(), linkedNode = null, loading = false }: Props = $props();

	const dispatch = createEventDispatcher<{
		create: { content: string; node_type: string; linkedNodeId?: string };
		close: void;
	}>();

	let content = $state('');
	let nodeType = $state('concept');

	function handleClose() {
		open = false;
		content = '';
		nodeType = 'concept';
		dispatch('close');
	}

	function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!content.trim()) return;

		dispatch('create', {
			content: content.trim(),
			node_type: nodeType,
			linkedNodeId: linkedNode?.id
		});
	}
</script>

<Dialog bind:open title={linkedNode ? 'Create Linked Node' : 'Create Node'} onclose={handleClose}>
	<form onsubmit={handleSubmit} class="space-y-4">
		{#if linkedNode}
			<div class="p-3 bg-gray-700/30 rounded-lg">
				<p class="text-xs text-gray-400 mb-1">Linking to:</p>
				<p class="text-sm text-gray-200 line-clamp-2">{linkedNode.content}</p>
			</div>
		{/if}

		<Textarea
			label="Content *"
			bind:value={content}
			placeholder="Enter the concept or idea..."
			rows={4}
			required
		/>

		<Input
			label="Type"
			bind:value={nodeType}
			placeholder="e.g., concept, idea, question"
		/>

		<div class="flex justify-end gap-3 pt-4">
			<Button type="button" variant="ghost" onclick={handleClose}>
				Cancel
			</Button>
			<Button type="submit" {loading}>
				{loading ? 'Creating...' : 'Create Node'}
			</Button>
		</div>
	</form>
</Dialog>
