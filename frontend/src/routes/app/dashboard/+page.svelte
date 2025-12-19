<script lang="ts">
	import { Card, Button } from '$lib/components/ui';
	import { user } from '$lib/stores';
	import { knowledgeBasesApi } from '$lib/api';
	import type { KnowledgeBaseListItem } from '$lib/api';
	import { onMount } from 'svelte';

	let recentKBs = $state<KnowledgeBaseListItem[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const response = await knowledgeBasesApi.listMine(1, 5);
			recentKBs = response.items;
		} catch {
			// Ignore errors
		} finally {
			loading = false;
		}
	});
</script>

<div class="animate-fade-in">
	<!-- Welcome Section -->
	<div class="mb-8">
		<h1 class="text-2xl font-bold text-gray-100">
			Welcome back, {$user?.username}!
		</h1>
		<p class="text-gray-400 mt-1">
			Here's an overview of your thought universe.
		</p>
	</div>

	<!-- Quick Actions -->
	<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
		<Card class="hover:border-cyan-500/50 transition-colors cursor-pointer">
			<a href="/app/knowledge-bases/new" class="block">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 bg-cyan-500/20 rounded-xl flex items-center justify-center text-2xl">
						➕
					</div>
					<div>
						<h3 class="font-semibold text-gray-100">New Knowledge Base</h3>
						<p class="text-sm text-gray-400">Start a new thought exploration</p>
					</div>
				</div>
			</a>
		</Card>

		<Card class="hover:border-cyan-500/50 transition-colors cursor-pointer">
			<a href="/app/knowledge-bases" class="block">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center text-2xl">
						📚
					</div>
					<div>
						<h3 class="font-semibold text-gray-100">Browse All</h3>
						<p class="text-sm text-gray-400">Explore knowledge bases</p>
					</div>
				</div>
			</a>
		</Card>

		<Card class="hover:border-cyan-500/50 transition-colors cursor-pointer">
			<a href="/app/profile" class="block">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center text-2xl">
						👤
					</div>
					<div>
						<h3 class="font-semibold text-gray-100">My Profile</h3>
						<p class="text-sm text-gray-400">View and edit your profile</p>
					</div>
				</div>
			</a>
		</Card>
	</div>

	<!-- Recent Knowledge Bases -->
	<Card>
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-lg font-semibold text-gray-100">Recent Knowledge Bases</h2>
			<a href="/app/knowledge-bases" class="text-sm text-cyan-400 hover:text-cyan-300">
				View all →
			</a>
		</div>

		{#if loading}
			<div class="flex justify-center py-8">
				<div class="animate-spin w-6 h-6 border-2 border-gray-600 border-t-cyan-400 rounded-full"></div>
			</div>
		{:else if recentKBs.length === 0}
			<div class="text-center py-8 text-gray-400">
				<p class="mb-4">You haven't created any knowledge bases yet.</p>
				<a href="/app/knowledge-bases/new">
					<Button>Create Your First</Button>
				</a>
			</div>
		{:else}
			<div class="space-y-3">
				{#each recentKBs as kb}
					<a
						href="/knowledge-bases/{kb.id}"
						class="block p-4 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 transition-colors"
					>
						<div class="flex items-center justify-between">
							<div>
								<h3 class="font-medium text-gray-100">{kb.name}</h3>
								{#if kb.description}
									<p class="text-sm text-gray-400 mt-1 line-clamp-1">{kb.description}</p>
								{/if}
							</div>
							<div class="flex items-center gap-2">
								{#if kb.is_public}
									<span class="px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded">Public</span>
								{:else}
									<span class="px-2 py-1 text-xs bg-gray-500/20 text-gray-400 rounded">Private</span>
								{/if}
							</div>
						</div>
					</a>
				{/each}
			</div>
		{/if}
	</Card>
</div>
