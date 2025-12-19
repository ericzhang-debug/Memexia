<script lang="ts">
	/**
	 * Node Edit Dialog
	 *
	 * Dialog for editing node content and type.
	 */
	import type { Node } from '$lib/api';
	import { Dialog, Button, Textarea, Input } from '$lib/components/ui';
	import { createEventDispatcher } from 'svelte';

	interface Props {
		open: boolean;
		node: Node | null;
		loading?: boolean;
	}

	let { open = $bindable(), node, loading = false }: Props = $props();

	const dispatch = createEventDispatcher<{
		save: { content: string; node_type: string };
		close: void;
	}>();

	let content = $state('');
	let nodeType = $state('');

	// Reset form when node changes
	$effect(() => {
		if (node) {
			content = node.content;
			nodeType = node.node_type;
		}
	});

	function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (!content.trim()) return;
		dispatch('save', { content: content.trim(), node_type: nodeType });
	}

	function handleClose() {
		open = false;
		dispatch('close');
	}
</script>

<Dialog bind:open title="Edit Node" onclose={handleClose}>
	<form onsubmit={handleSubmit} class="space-y-4">
		<Textarea
			label="Content"
			bind:value={content}
			placeholder="Node content..."
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
				{loading ? 'Saving...' : 'Save Changes'}
			</Button>
		</div>
	</form>
</Dialog>
