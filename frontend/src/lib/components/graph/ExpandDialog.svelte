<script lang="ts">
	/**
	 * AI Expand Dialog
	 *
	 * Dialog for AI-powered node expansion with streaming output.
	 */
	import type { Node, StreamingNodeEvent } from '$lib/api';
	import { Dialog, Button, Textarea } from '$lib/components/ui';
	import { createEventDispatcher } from 'svelte';
	import { nodesApi } from '$lib/api';
	import { toast } from '$lib/stores/toast';

	interface Props {
		open: boolean;
		node: Node | null;
		kbId: string;
	}

	let { open = $bindable(), node, kbId }: Props = $props();

	const dispatch = createEventDispatcher<{
		expanded: Node[];
		close: void;
	}>();

	let instruction = $state('');
	let loading = $state(false);
	let streamOutput = $state<string[]>([]);
	let aiResponse = $state('');
	let createdNodes = $state<Node[]>([]);
	let abortController: AbortController | null = null;

	function handleClose() {
		if (loading && abortController) {
			abortController.abort();
		}
		open = false;
		instruction = '';
		streamOutput = [];
		aiResponse = '';
		createdNodes = [];
		dispatch('close');
	}

	function handleEvent(event: StreamingNodeEvent) {
		switch (event.type) {
			case 'start':
				streamOutput = [...streamOutput, `Analyzing: "${event.source_node.content.slice(0, 50)}..."`];
				break;

			case 'thinking':
				streamOutput = [...streamOutput, `💭 ${event.message}`];
				break;

			case 'chunk':
				// Accumulate AI response chunks
				aiResponse += event.content;
				break;

			case 'parsing':
				streamOutput = [...streamOutput, `⚙️ ${event.message}`];
				break;

			case 'node_created':
				const newNode: Node = {
					id: event.node.id,
					content: event.node.content,
					node_type: event.node.node_type,
					created_at: new Date().toISOString(),
					updated_at: null
				};
				createdNodes = [...createdNodes, newNode];
				streamOutput = [...streamOutput, `✨ Created: ${event.node.content.slice(0, 50)}...`];
				break;

			case 'complete':
				streamOutput = [...streamOutput, `✅ Complete! Created ${event.total_nodes} nodes.`];
				break;

			case 'error':
				streamOutput = [...streamOutput, `❌ Error: ${event.message}`];
				break;
		}
	}

	async function handleExpand(e: SubmitEvent) {
		e.preventDefault();
		if (!node) return;

		loading = true;
		streamOutput = ['🚀 Starting AI expansion...'];
		aiResponse = '';
		createdNodes = [];
		abortController = new AbortController();

		try {
			// Try streaming endpoint first
			try {
				for await (const event of nodesApi.expandStream(
					kbId,
					node.id,
					{ instruction: instruction.trim() || undefined },
					abortController.signal
				)) {
					handleEvent(event);
				}
			} catch (streamError) {
				// Fallback to non-streaming endpoint
				console.warn('Streaming failed, using fallback:', streamError);
				streamOutput = [...streamOutput, '📡 Using fallback method...'];
				const nodes = await nodesApi.expand(kbId, node.id, {
					instruction: instruction.trim() || undefined
				});
				createdNodes = nodes;
				streamOutput = [
					...streamOutput,
					...nodes.map((n) => `✨ Created: ${n.content.slice(0, 50)}...`),
					`✅ Complete! Created ${nodes.length} nodes.`
				];
			}

			if (createdNodes.length > 0) {
				toast.success(`Created ${createdNodes.length} new nodes`);
				dispatch('expanded', createdNodes);
			} else {
				toast.info('No new nodes were created');
			}
		} catch (err: unknown) {
			if (err instanceof Error && err.name === 'AbortError') {
				streamOutput = [...streamOutput, '⏹️ Expansion cancelled.'];
			} else {
				const message = err instanceof Error ? err.message : 'Expansion failed';
				streamOutput = [...streamOutput, `❌ Error: ${message}`];
				toast.error(message);
			}
		} finally {
			loading = false;
			abortController = null;
		}
	}

	function handleCancel() {
		if (abortController) {
			abortController.abort();
		}
	}
</script>

<Dialog bind:open title="AI Expand Node" onclose={handleClose}>
	{#if node}
		<div class="space-y-4">
			<!-- Source Node Preview -->
			<div class="p-3 bg-gray-700/30 rounded-lg">
				<p class="text-xs text-gray-400 mb-1">Expanding from:</p>
				<p class="text-sm text-gray-200 line-clamp-3">{node.content}</p>
			</div>

			{#if !loading && createdNodes.length === 0}
				<!-- Input Form -->
				<form onsubmit={handleExpand}>
					<Textarea
						label="Expansion Instruction (optional)"
						bind:value={instruction}
						placeholder="e.g., Focus on practical applications, or explore philosophical implications..."
						rows={3}
					/>

					<div class="flex justify-end gap-3 pt-4">
						<Button type="button" variant="ghost" onclick={handleClose}>
							Cancel
						</Button>
						<Button type="submit">
							<span class="mr-2">🧠</span>
							Start Expansion
						</Button>
					</div>
				</form>
			{:else}
				<!-- Streaming Output -->
				<div class="space-y-2">
					<p class="text-sm font-medium text-gray-300">Progress:</p>
					<div class="p-3 bg-gray-900 rounded-lg max-h-48 overflow-y-auto font-mono text-xs">
						{#each streamOutput as line}
							<p class="text-gray-400 py-0.5">{line}</p>
						{/each}
						{#if loading}
							<p class="text-cyan-400 animate-pulse">Processing...</p>
						{/if}
					</div>
				</div>

				<!-- AI Response Preview (if chunks accumulated) -->
				{#if aiResponse}
					<div class="space-y-2">
						<p class="text-sm font-medium text-gray-300">AI Response:</p>
						<div class="p-3 bg-gray-800 rounded-lg max-h-32 overflow-y-auto text-xs text-gray-300 whitespace-pre-wrap">
							{aiResponse}
						</div>
					</div>
				{/if}

				<!-- Created Nodes Preview -->
				{#if createdNodes.length > 0}
					<div class="space-y-2">
						<p class="text-sm font-medium text-gray-300">Created Nodes ({createdNodes.length}):</p>
						<div class="space-y-2 max-h-32 overflow-y-auto">
							{#each createdNodes as newNode}
								<div class="p-2 bg-cyan-500/10 border border-cyan-500/30 rounded text-sm text-gray-200">
									{newNode.content.slice(0, 100)}{newNode.content.length > 100 ? '...' : ''}
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Actions -->
				<div class="flex justify-end gap-3 pt-4">
					{#if loading}
						<Button variant="danger" onclick={handleCancel}>
							Cancel
						</Button>
					{:else}
						<Button onclick={handleClose}>
							{createdNodes.length > 0 ? 'Done' : 'Close'}
						</Button>
					{/if}
				</div>
			{/if}
		</div>
	{/if}
</Dialog>
