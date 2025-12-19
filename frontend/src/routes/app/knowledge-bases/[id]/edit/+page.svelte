<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Card, Button, Input, Textarea, Toggle, Loading } from '$lib/components/ui';
	import { knowledgeBasesApi } from '$lib/api';
	import type { KnowledgeBase } from '$lib/api';
	import { toast } from '$lib/stores/toast';
	import type { ApiError } from '$lib/api';

	const kbId = $derived($page.params.id);

	let kb = $state<KnowledgeBase | null>(null);
	let loading = $state(true);
	let saving = $state(false);

	let name = $state('');
	let description = $state('');
	let isPublic = $state(false);
	let error = $state('');

	onMount(async () => {
		try {
			if (!kbId) {
				throw new Error('Knowledge base ID is missing');
			}
			kb = await knowledgeBasesApi.get(kbId);
			name = kb.name;
			description = kb.description || '';
			isPublic = kb.is_public;
		} catch (err) {
			toast.error('Failed to load knowledge base');
			goto('/app/knowledge-bases');
		} finally {
			loading = false;
		}
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';

		if (!name.trim()) {
			error = 'Name is required';
			return;
		}

		saving = true;

		try {
			if (!kbId) {
				throw new Error('Knowledge base ID is missing');
			}
			await knowledgeBasesApi.update(kbId, {
				name: name.trim(),
				description: description.trim() || undefined,
				is_public: isPublic
			});

			toast.success('Knowledge base updated!');
			goto(`/app/knowledge-bases/${kbId}`);
		} catch (err) {
			const apiError = err as ApiError;
			error = apiError.message || 'Failed to update knowledge base';
			toast.error(error);
		} finally {
			saving = false;
		}
	}
</script>

{#if loading}
	<div class="flex justify-center py-16">
		<Loading size="lg" />
	</div>
{:else if kb}
	<div class="animate-fade-in max-w-2xl mx-auto">
		<div class="mb-6">
			<a href="/app/knowledge-bases/{kbId}" class="text-sm text-gray-400 hover:text-gray-300">
				← Back to {kb.name}
			</a>
		</div>

		<h1 class="text-2xl font-bold text-gray-100 mb-6">Edit Knowledge Base</h1>

		<Card>
			<form onsubmit={handleSubmit} class="space-y-6">
				<Input
					label="Name *"
					bind:value={name}
					placeholder="e.g., Philosophy of Mind"
					required
					maxlength={100}
				/>

				<Textarea
					label="Description"
					bind:value={description}
					placeholder="A brief description of this knowledge base..."
					rows={3}
					maxlength={500}
				/>

				<div class="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg">
					<div>
						<p class="font-medium text-gray-200">Make Public</p>
						<p class="text-sm text-gray-400">Allow others to view and copy this knowledge base</p>
					</div>
					<Toggle bind:checked={isPublic} />
				</div>

				<div class="p-4 bg-gray-700/20 rounded-lg border border-gray-600">
					<p class="text-sm text-gray-400">
						<strong>Note:</strong> The seed concept cannot be changed after creation.
						You can modify the seed node's content from the 3D explore view.
					</p>
				</div>

				{#if error}
					<p class="text-red-400 text-sm">{error}</p>
				{/if}

				<div class="flex items-center gap-4">
					<Button type="submit" loading={saving} class="flex-1">
						{saving ? 'Saving...' : 'Save Changes'}
					</Button>
					<a href="/app/knowledge-bases/{kbId}">
						<Button type="button" variant="ghost">Cancel</Button>
					</a>
				</div>
			</form>
		</Card>
	</div>
{/if}
