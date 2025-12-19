<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, Loading } from '$lib/components/ui';
	import { usersApi, knowledgeBasesApi } from '$lib/api';

	let stats = $state({
		totalUsers: 0,
		totalKnowledgeBases: 0,
		publicKnowledgeBases: 0
	});
	let loading = $state(true);

	onMount(async () => {
		try {
			const [users, kbs] = await Promise.all([
				usersApi.list(0, 1000),
				knowledgeBasesApi.list(1, 100, false)
			]);

			stats.totalUsers = users.length;
			stats.totalKnowledgeBases = kbs.total;
			stats.publicKnowledgeBases = kbs.items.filter((kb) => kb.is_public).length;
		} catch {
			// Ignore errors
		} finally {
			loading = false;
		}
	});
</script>

<div class="animate-fade-in">
	<h1 class="text-2xl font-bold text-gray-100 mb-6">Admin Dashboard</h1>

	{#if loading}
		<Loading size="lg" class="py-8" />
	{:else}
		<!-- Stats Grid -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
			<Card>
				<div class="flex items-center gap-4">
					<div class="w-14 h-14 bg-cyan-500/20 rounded-xl flex items-center justify-center text-2xl">
						👥
					</div>
					<div>
						<p class="text-3xl font-bold text-gray-100">{stats.totalUsers}</p>
						<p class="text-sm text-gray-400">Total Users</p>
					</div>
				</div>
			</Card>

			<Card>
				<div class="flex items-center gap-4">
					<div class="w-14 h-14 bg-purple-500/20 rounded-xl flex items-center justify-center text-2xl">
						📚
					</div>
					<div>
						<p class="text-3xl font-bold text-gray-100">{stats.totalKnowledgeBases}</p>
						<p class="text-sm text-gray-400">Knowledge Bases</p>
					</div>
				</div>
			</Card>

			<Card>
				<div class="flex items-center gap-4">
					<div class="w-14 h-14 bg-green-500/20 rounded-xl flex items-center justify-center text-2xl">
						🌐
					</div>
					<div>
						<p class="text-3xl font-bold text-gray-100">{stats.publicKnowledgeBases}</p>
						<p class="text-sm text-gray-400">Public KBs</p>
					</div>
				</div>
			</Card>
		</div>

		<!-- Quick Actions -->
		<Card>
			<h2 class="text-lg font-semibold text-gray-100 mb-4">Quick Actions</h2>
			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<a
					href="/admin/users"
					class="p-4 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 transition-colors"
				>
					<div class="flex items-center gap-3">
						<span class="text-2xl">👥</span>
						<div>
							<p class="font-medium text-gray-100">Manage Users</p>
							<p class="text-sm text-gray-400">View and manage user accounts</p>
						</div>
					</div>
				</a>

				<a
					href="/admin/settings"
					class="p-4 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 transition-colors"
				>
					<div class="flex items-center gap-3">
						<span class="text-2xl">⚙️</span>
						<div>
							<p class="font-medium text-gray-100">System Settings</p>
							<p class="text-sm text-gray-400">Configure authentication and database</p>
						</div>
					</div>
				</a>
			</div>
		</Card>
	{/if}
</div>
