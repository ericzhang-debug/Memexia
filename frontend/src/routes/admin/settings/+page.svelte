<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, Button, Loading, Toggle, Input } from '$lib/components/ui';
	import { adminApi } from '$lib/api';
	import type { AuthSettings, GraphDBSettings } from '$lib/api';
	import { toast } from '$lib/stores/toast';

	let authSettings = $state<AuthSettings | null>(null);
	let graphSettings = $state<GraphDBSettings | null>(null);
	let loading = $state(true);

	let authSaving = $state(false);
	let graphSaving = $state(false);

	async function loadSettings() {
		loading = true;
		try {
			const [auth, graph] = await Promise.all([
				adminApi.getAuthSettings(),
				adminApi.getGraphDBSettings()
			]);
			authSettings = auth;
			graphSettings = graph;
		} catch (err) {
			toast.error('Failed to load settings');
		} finally {
			loading = false;
		}
	}

	onMount(loadSettings);

	async function saveAuthSettings() {
		if (!authSettings) return;
		authSaving = true;

		try {
			await adminApi.updateAuthSettings(authSettings);
			toast.success('Authentication settings saved');
		} catch (err) {
			toast.error('Failed to save settings');
		} finally {
			authSaving = false;
		}
	}

	async function saveGraphSettings() {
		if (!graphSettings) return;
		graphSaving = true;

		try {
			await adminApi.updateGraphDBSettings(graphSettings);
			toast.success('Database settings saved. Restart required for changes to take effect.');
		} catch (err) {
			toast.error('Failed to save settings');
		} finally {
			graphSaving = false;
		}
	}
</script>

<div class="animate-fade-in max-w-3xl">
	<h1 class="text-2xl font-bold text-gray-100 mb-6">System Settings</h1>

	{#if loading}
		<Loading size="lg" class="py-8" />
	{:else}
		<!-- Authentication Settings -->
		<Card class="mb-6">
			<h2 class="text-lg font-semibold text-gray-100 mb-4">Authentication Settings</h2>
			<p class="text-sm text-gray-400 mb-6">
				Configure verification requirements for user registration.
			</p>

			{#if authSettings}
				<div class="space-y-4">
					<div class="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg">
						<div>
							<p class="font-medium text-gray-200">Email Verification</p>
							<p class="text-sm text-gray-400">Require email verification on registration</p>
						</div>
						<Toggle bind:checked={authSettings.enable_email} />
					</div>

					<div class="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg">
						<div>
							<p class="font-medium text-gray-200">Phone Verification</p>
							<p class="text-sm text-gray-400">Require phone verification (not implemented)</p>
						</div>
						<Toggle bind:checked={authSettings.enable_phone} disabled />
					</div>

					<div class="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg">
						<div>
							<p class="font-medium text-gray-200">QQ Verification</p>
							<p class="text-sm text-gray-400">Require QQ verification (not implemented)</p>
						</div>
						<Toggle bind:checked={authSettings.enable_qq} disabled />
					</div>

					<div class="flex justify-end pt-4">
						<Button onclick={saveAuthSettings} loading={authSaving}>
							{authSaving ? 'Saving...' : 'Save Auth Settings'}
						</Button>
					</div>
				</div>
			{/if}
		</Card>

		<!-- Graph Database Settings -->
		<Card>
			<h2 class="text-lg font-semibold text-gray-100 mb-4">Graph Database Settings</h2>
			<p class="text-sm text-gray-400 mb-6">
				Configure the graph database backend. Changes require an application restart.
			</p>

			{#if graphSettings}
				<div class="space-y-6">
					<!-- Database Type -->
					<div>
						<label class="block text-sm font-medium text-gray-300 mb-2">Database Type</label>
						<div class="grid grid-cols-2 gap-3">
							<label
								class="flex items-center gap-3 p-4 bg-gray-700/30 rounded-lg cursor-pointer hover:bg-gray-700/50 border-2 transition-colors
									{graphSettings.db_type === 'kuzu' ? 'border-cyan-500' : 'border-transparent'}"
							>
								<input
									type="radio"
									name="db_type"
									value="kuzu"
									bind:group={graphSettings.db_type}
									class="w-4 h-4 text-cyan-500"
								/>
								<div>
									<p class="font-medium text-gray-100">Kuzu</p>
									<p class="text-xs text-gray-400">Embedded (default)</p>
								</div>
							</label>

							<label
								class="flex items-center gap-3 p-4 bg-gray-700/30 rounded-lg cursor-pointer hover:bg-gray-700/50 border-2 transition-colors
									{graphSettings.db_type === 'nebula' ? 'border-cyan-500' : 'border-transparent'}"
							>
								<input
									type="radio"
									name="db_type"
									value="nebula"
									bind:group={graphSettings.db_type}
									class="w-4 h-4 text-cyan-500"
								/>
								<div>
									<p class="font-medium text-gray-100">NebulaGraph</p>
									<p class="text-xs text-gray-400">Remote cluster</p>
								</div>
							</label>
						</div>
					</div>

					{#if graphSettings.db_type === 'kuzu'}
						<!-- Kuzu Settings -->
						<Input
							label="Database Path"
							bind:value={graphSettings.kuzu_db_path}
							placeholder="./data/kuzu_db"
						/>
					{:else}
						<!-- NebulaGraph Settings -->
						<div class="grid grid-cols-2 gap-4">
							<Input
								label="Host"
								bind:value={graphSettings.nebula_host}
								placeholder="127.0.0.1"
							/>
							<Input
								label="Port"
								type="number"
								bind:value={graphSettings.nebula_port}
								placeholder="9669"
							/>
						</div>
						<div class="grid grid-cols-2 gap-4">
							<Input
								label="Username"
								bind:value={graphSettings.nebula_user}
								placeholder="root"
							/>
							<Input
								label="Password"
								type="password"
								bind:value={graphSettings.nebula_password}
								placeholder="••••••••"
							/>
						</div>
					{/if}

					<div class="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
						<p class="text-sm text-yellow-400">
							<strong>Note:</strong> Changing database settings requires restarting the backend
							server for changes to take effect.
						</p>
					</div>

					<div class="flex justify-end pt-4">
						<Button onclick={saveGraphSettings} loading={graphSaving}>
							{graphSaving ? 'Saving...' : 'Save Database Settings'}
						</Button>
					</div>
				</div>
			{/if}
		</Card>
	{/if}
</div>
