<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Card, Button, Loading, Dialog } from '$lib/components/ui';
	import { knowledgeBasesApi, nodesApi } from '$lib/api';
	import type { KnowledgeBase, GraphData } from '$lib/api';
	import { toast } from '$lib/stores/toast';
	import { user } from '$lib/stores';

	const kbId = $derived($page.params.id);

	let kb = $state<KnowledgeBase | null>(null);
	let graphData = $state<GraphData | null>(null);
	let loading = $state(true);
	let deleteDialogOpen = $state(false);
	let deleting = $state(false);

	const canEdit = $derived(
		kb && $user && (kb.owner_id === $user.id || $user.is_superuser || $user.role === 'admin')
	);

	onMount(async () => {
		try {
			const [kbData, graph] = await Promise.all([
				knowledgeBasesApi.get(kbId),
				nodesApi.getGraphData(kbId)
			]);
			kb = kbData;
			graphData = graph;
		} catch (err) {
			toast.error('Failed to load knowledge base');
			goto('/app/knowledge-bases');
		} finally {
			loading = false;
		}
	});

	async function handleDelete() {
		if (!kb) return;
		deleting = true;

		try {
			await knowledgeBasesApi.delete(kbId);
			toast.success('Knowledge base deleted');
			goto('/app/knowledge-bases');
		} catch (err) {
			toast.error('Failed to delete knowledge base');
		} finally {
			deleting = false;
			deleteDialogOpen = false;
		}
	}
</script>

{#if loading}
	<div class="flex justify-center py-16">
		<Loading size="lg" />
	</div>
{:else if kb}
	<div class="animate-fade-in">
		<!-- Back Link -->
		<div class="mb-6">
			<a href="/app/knowledge-bases" class="text-sm text-gray-400 hover:text-gray-300">
				← Back to Knowledge Bases
			</a>
		</div>

		<!-- Header -->
		<div class="flex items-start justify-between mb-8">
			<div>
				<div class="flex items-center gap-3 mb-2">
					<h1 class="text-2xl font-bold text-gray-100">{kb.name}</h1>
					{#if kb.is_public}
						<span class="px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded">Public</span>
					{:else}
						<span class="px-2 py-1 text-xs bg-gray-500/20 text-gray-400 rounded">Private</span>
					{/if}
				</div>
				{#if kb.description}
					<p class="text-gray-400 max-w-2xl">{kb.description}</p>
				{/if}
			</div>

			<div class="flex items-center gap-3">
				<a href="/app/knowledge-bases/{kbId}/explore">
					<Button>
						<span class="mr-2">🌐</span>
						Explore in 3D
					</Button>
				</a>
				{#if canEdit}
					<a href="/app/knowledge-bases/{kbId}/edit">
						<Button variant="secondary">Edit</Button>
					</a>
					<Button variant="danger" onclick={() => (deleteDialogOpen = true)}>
						Delete
					</Button>
				{/if}
			</div>
		</div>

		<!-- Stats Cards -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
			<Card padding="sm">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 bg-cyan-500/20 rounded-xl flex items-center justify-center text-2xl">
						🧠
					</div>
					<div>
						<p class="text-2xl font-bold text-gray-100">{graphData?.nodes.length || 0}</p>
						<p class="text-sm text-gray-400">Nodes</p>
					</div>
				</div>
			</Card>

			<Card padding="sm">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center text-2xl">
						🔗
					</div>
					<div>
						<p class="text-2xl font-bold text-gray-100">{graphData?.edges.length || 0}</p>
						<p class="text-sm text-gray-400">Connections</p>
					</div>
				</div>
			</Card>

			<Card padding="sm">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center text-2xl">
						📅
					</div>
					<div>
						<p class="text-sm font-bold text-gray-100">
							{new Date(kb.created_at).toLocaleDateString()}
						</p>
						<p class="text-sm text-gray-400">Created</p>
					</div>
				</div>
			</Card>
		</div>

		<!-- Node Preview (Simplified 2D view) -->
		<Card>
			<h2 class="text-lg font-semibold text-gray-100 mb-4">Nodes Overview</h2>

			{#if !graphData || graphData.nodes.length === 0}
				<div class="text-center py-8 text-gray-400">
					<p>No nodes yet. Start exploring to expand your knowledge!</p>
					<a href="/app/knowledge-bases/{kbId}/explore" class="mt-4 inline-block">
						<Button>Start Exploring</Button>
					</a>
				</div>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-96 overflow-y-auto">
					{#each graphData.nodes.slice(0, 12) as node}
						<div class="p-3 bg-gray-700/30 rounded-lg">
							<div class="flex items-start justify-between mb-2">
								<span class="px-2 py-0.5 text-xs bg-cyan-500/20 text-cyan-400 rounded">
									{node.node_type}
								</span>
								{#if node.id === kb.seed_node_id}
									<span class="px-2 py-0.5 text-xs bg-yellow-500/20 text-yellow-400 rounded">
										Seed
									</span>
								{/if}
							</div>
							<p class="text-sm text-gray-200 line-clamp-3">{node.content}</p>
						</div>
					{/each}
				</div>

				{#if graphData.nodes.length > 12}
					<p class="text-center text-sm text-gray-500 mt-4">
						Showing 12 of {graphData.nodes.length} nodes.
						<a href="/app/knowledge-bases/{kbId}/explore" class="text-cyan-400 hover:text-cyan-300">
							View all in 3D
						</a>
					</p>
				{/if}
			{/if}
		</Card>
	</div>

	<!-- Delete Confirmation Dialog -->
	<Dialog bind:open={deleteDialogOpen} title="Delete Knowledge Base">
		<p class="text-gray-300 mb-6">
			Are you sure you want to delete <strong>"{kb.name}"</strong>? This action cannot be undone
			and all associated nodes will be permanently removed.
		</p>
		<div class="flex justify-end gap-3">
			<Button variant="ghost" onclick={() => (deleteDialogOpen = false)}>Cancel</Button>
			<Button variant="danger" onclick={handleDelete} loading={deleting}>
				{deleting ? 'Deleting...' : 'Delete'}
			</Button>
		</div>
	</Dialog>
{/if}
