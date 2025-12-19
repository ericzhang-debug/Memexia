<script lang="ts">
	/**
	 * 3D Knowledge Base Explorer
	 *
	 * Full-screen 3D graph visualization for exploring knowledge bases.
	 */
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Button, Loading, Dialog } from '$lib/components/ui';
	import {
		ThreeGraph,
		NodePopup,
		NodeEditDialog,
		ExpandDialog,
		CreateNodeDialog
	} from '$lib/components/graph';
	import { knowledgeBasesApi, nodesApi } from '$lib/api';
	import type { KnowledgeBase, GraphData, Node } from '$lib/api';
	import { toast } from '$lib/stores/toast';
	import { user } from '$lib/stores';

	const kbId = $derived($page.params.id);

	let kb = $state<KnowledgeBase | null>(null);
	let graphData = $state<GraphData>({ nodes: [], edges: [] });
	let loading = $state(true);

	// Selected node state
	let selectedNode = $state<Node | null>(null);
	let popupPosition = $state({ x: 0, y: 0 });

	// Dialog states
	let editDialogOpen = $state(false);
	let editingNode = $state<Node | null>(null);
	let editLoading = $state(false);

	let expandDialogOpen = $state(false);
	let expandingNode = $state<Node | null>(null);

	let createDialogOpen = $state(false);
	let linkedNode = $state<Node | null>(null);
	let createLoading = $state(false);

	let deleteDialogOpen = $state(false);
	let deletingNode = $state<Node | null>(null);
	let deleteLoading = $state(false);

	const canEdit = $derived(
		kb && $user && (kb.owner_id === $user.id || $user.is_superuser || $user.role === 'admin')
	);

	async function loadData() {
		loading = true;
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
	}

	onMount(loadData);

	function handleNodeClick(e: CustomEvent<{ node: Node; position: { x: number; y: number } }>) {
		selectedNode = e.detail.node;
		popupPosition = e.detail.position;
	}

	function closePopup() {
		selectedNode = null;
	}

	// Edit handlers
	function openEditDialog(node: Node) {
		editingNode = node;
		editDialogOpen = true;
		selectedNode = null;
	}

	async function handleSaveEdit(e: CustomEvent<{ content: string; node_type: string }>) {
		if (!editingNode) return;
		editLoading = true;

		try {
			await nodesApi.update(kbId, editingNode.id, {
				content: e.detail.content,
				node_type: e.detail.node_type
			});
			toast.success('Node updated');
			editDialogOpen = false;
			await loadData();
		} catch (err) {
			toast.error('Failed to update node');
		} finally {
			editLoading = false;
		}
	}

	// Expand handlers
	function openExpandDialog(node: Node) {
		expandingNode = node;
		expandDialogOpen = true;
		selectedNode = null;
	}

	async function handleExpanded() {
		expandDialogOpen = false;
		await loadData();
	}

	// Create handlers
	function openCreateDialog(node?: Node) {
		linkedNode = node || null;
		createDialogOpen = true;
		selectedNode = null;
	}

	async function handleCreate(
		e: CustomEvent<{ content: string; node_type: string; linkedNodeId?: string }>
	) {
		createLoading = true;

		try {
			const newNode = await nodesApi.create(kbId, {
				content: e.detail.content,
				node_type: e.detail.node_type
			});

			// TODO: Create edge if linkedNodeId is provided
			// This would require a backend endpoint for edge creation

			toast.success('Node created');
			createDialogOpen = false;
			await loadData();
		} catch (err) {
			toast.error('Failed to create node');
		} finally {
			createLoading = false;
		}
	}

	// Delete handlers
	function openDeleteDialog(node: Node) {
		deletingNode = node;
		deleteDialogOpen = true;
		selectedNode = null;
	}

	async function handleDelete() {
		if (!deletingNode) return;
		deleteLoading = true;

		try {
			await nodesApi.delete(kbId, deletingNode.id);
			toast.success('Node deleted');
			deleteDialogOpen = false;
			await loadData();
		} catch (err) {
			toast.error('Failed to delete node');
		} finally {
			deleteLoading = false;
			deletingNode = null;
		}
	}
</script>

<svelte:head>
	<title>{kb?.name || 'Explore'} - Memexia</title>
</svelte:head>

{#if loading}
	<div class="fixed inset-0 flex items-center justify-center bg-gray-900">
		<Loading size="lg" />
	</div>
{:else if kb}
	<!-- Full screen container -->
	<div class="fixed inset-0 bg-gray-900">
		<!-- Top Bar -->
		<div class="absolute top-0 left-0 right-0 z-30 bg-gray-900/80 backdrop-blur-sm border-b border-gray-700">
			<div class="flex items-center justify-between px-4 py-3">
				<div class="flex items-center gap-4">
					<a
						href="/knowledge-bases/{kbId}"
						class="text-gray-400 hover:text-gray-200 transition-colors"
					>
						← Back
					</a>
					<div>
						<h1 class="text-lg font-semibold text-gray-100">{kb.name}</h1>
						<p class="text-xs text-gray-400">
							{graphData.nodes.length} nodes · {graphData.edges.length} connections
						</p>
					</div>
				</div>

				{#if canEdit}
					<div class="flex items-center gap-2">
						<Button size="sm" onclick={() => openCreateDialog()}>
							+ Add Node
						</Button>
					</div>
				{/if}
			</div>
		</div>

		<!-- 3D Graph -->
		<ThreeGraph
			nodes={graphData.nodes}
			edges={graphData.edges}
			seedNodeId={kb.seed_node_id}
			on:nodeClick={handleNodeClick}
		/>

		<!-- Node Popup -->
		<NodePopup
			node={selectedNode}
			position={popupPosition}
			isSeedNode={selectedNode?.id === kb.seed_node_id}
			canEdit={canEdit ?? false}
			on:close={closePopup}
			on:edit={(e) => openEditDialog(e.detail)}
			on:delete={(e) => openDeleteDialog(e.detail)}
			on:expand={(e) => openExpandDialog(e.detail)}
			on:createLinked={(e) => openCreateDialog(e.detail)}
		/>

		<!-- Controls Help -->
		<div class="absolute bottom-4 left-4 z-20 p-3 bg-gray-800/80 backdrop-blur-sm rounded-lg text-xs text-gray-400">
			<p><strong>Controls:</strong></p>
			<p>Mouse drag: Rotate view</p>
			<p>Scroll: Zoom</p>
			<p>WASD/Arrows: Move</p>
			<p>Q/E: Up/Down</p>
			<p>Click node: Details</p>
		</div>

		<!-- Legend -->
		<div class="absolute bottom-4 right-4 z-20 p-3 bg-gray-800/80 backdrop-blur-sm rounded-lg text-xs">
			<p class="text-gray-400 mb-2"><strong>Legend:</strong></p>
			<div class="flex items-center gap-2 mb-1">
				<span class="w-3 h-3 rounded-full bg-yellow-400"></span>
				<span class="text-gray-300">Seed Node</span>
			</div>
			<div class="flex items-center gap-2 mb-1">
				<span class="w-3 h-3 rounded-full bg-cyan-400"></span>
				<span class="text-gray-300">AI Generated</span>
			</div>
			<div class="flex items-center gap-2">
				<span class="w-3 h-3 rounded-full bg-purple-400"></span>
				<span class="text-gray-300">Manual</span>
			</div>
		</div>
	</div>

	<!-- Dialogs -->
	<NodeEditDialog
		bind:open={editDialogOpen}
		node={editingNode}
		loading={editLoading}
		on:save={handleSaveEdit}
	/>

	<ExpandDialog
		bind:open={expandDialogOpen}
		node={expandingNode}
		{kbId}
		on:expanded={handleExpanded}
	/>

	<CreateNodeDialog
		bind:open={createDialogOpen}
		{linkedNode}
		loading={createLoading}
		on:create={handleCreate}
	/>

	<Dialog bind:open={deleteDialogOpen} title="Delete Node">
		<p class="text-gray-300 mb-4">
			Are you sure you want to delete this node? This action cannot be undone.
		</p>
		{#if deletingNode}
			<div class="p-3 bg-gray-700/30 rounded-lg mb-6">
				<p class="text-sm text-gray-200">{deletingNode.content}</p>
			</div>
		{/if}
		<div class="flex justify-end gap-3">
			<Button variant="ghost" onclick={() => (deleteDialogOpen = false)}>Cancel</Button>
			<Button variant="danger" onclick={handleDelete} loading={deleteLoading}>
				{deleteLoading ? 'Deleting...' : 'Delete'}
			</Button>
		</div>
	</Dialog>
{/if}

<style>
	/* Override layout for full-screen mode */
	:global(body) {
		overflow: hidden;
	}
</style>
