<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, Button, Pagination, Loading } from '$lib/components/ui';
	import { knowledgeBasesApi } from '$lib/api';
	import type { KnowledgeBaseListItem, PaginatedKnowledgeBases } from '$lib/api';
	import { toast } from '$lib/stores/toast';

	let data = $state<PaginatedKnowledgeBases | null>(null);
	let loading = $state(true);
	let page = $state(1);
	let mineOnly = $state(false);

	async function loadKnowledgeBases() {
		loading = true;
		try {
			data = await knowledgeBasesApi.list(page, 12, mineOnly);
		} catch (err) {
			toast.error('Failed to load knowledge bases');
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadKnowledgeBases();
	});

	function handlePageChange(newPage: number) {
		page = newPage;
		loadKnowledgeBases();
	}

	function handleFilterChange() {
		page = 1;
		loadKnowledgeBases();
	}
</script>

<div class="animate-fade-in">
	<!-- Header -->
	<div class="flex items-center justify-between mb-6">
		<div>
			<h1 class="text-2xl font-bold text-gray-100">Knowledge Bases</h1>
			<p class="text-gray-400 mt-1">Explore and manage your thought universes</p>
		</div>
		<a href="/app/knowledge-bases/new">
			<Button>
				<span class="mr-2">+</span>
				New Knowledge Base
			</Button>
		</a>
	</div>

	<!-- Filters -->
	<div class="flex items-center gap-4 mb-6">
		<button
			onclick={() => { mineOnly = false; handleFilterChange(); }}
			class="px-4 py-2 rounded-lg text-sm font-medium transition-colors
				{!mineOnly ? 'bg-cyan-500 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}"
		>
			All
		</button>
		<button
			onclick={() => { mineOnly = true; handleFilterChange(); }}
			class="px-4 py-2 rounded-lg text-sm font-medium transition-colors
				{mineOnly ? 'bg-cyan-500 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}"
		>
			My Knowledge Bases
		</button>
	</div>

	<!-- Content -->
	{#if loading}
		<div class="flex justify-center py-16">
			<Loading size="lg" />
		</div>
	{:else if !data || data.items.length === 0}
		<Card class="text-center py-16">
			<div class="text-4xl mb-4">📚</div>
			<h2 class="text-xl font-semibold text-gray-100 mb-2">No Knowledge Bases Found</h2>
			<p class="text-gray-400 mb-6">
				{mineOnly ? "You haven't created any knowledge bases yet." : "No knowledge bases available."}
			</p>
			<a href="/app/knowledge-bases/new">
				<Button>Create Your First</Button>
			</a>
		</Card>
	{:else}
		<!-- Grid -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
			{#each data.items as kb}
				<a href="/app/knowledge-bases/{kb.id}" class="block">
					<Card class="h-full hover:border-cyan-500/50 transition-all hover:-translate-y-1">
						<div class="flex items-start justify-between mb-3">
							<h3 class="font-semibold text-gray-100 line-clamp-1">{kb.name}</h3>
							{#if kb.is_public}
								<span class="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded shrink-0 ml-2">
									Public
								</span>
							{:else}
								<span class="px-2 py-0.5 text-xs bg-gray-500/20 text-gray-400 rounded shrink-0 ml-2">
									Private
								</span>
							{/if}
						</div>
						{#if kb.description}
							<p class="text-sm text-gray-400 line-clamp-2 mb-4">{kb.description}</p>
						{:else}
							<p class="text-sm text-gray-500 italic mb-4">No description</p>
						{/if}
						<div class="text-xs text-gray-500 mt-auto">
							Created {new Date(kb.created_at).toLocaleDateString()}
						</div>
					</Card>
				</a>
			{/each}
		</div>

		<!-- Pagination -->
		{#if data.total_pages > 1}
			<div class="flex justify-center">
				<Pagination
					{page}
					totalPages={data.total_pages}
					onchange={handlePageChange}
				/>
			</div>
		{/if}
	{/if}
</div>
