<script lang="ts">
	import { goto } from '$app/navigation';
	import { Card, Button, Input, Textarea, Toggle } from '$lib/components/ui';
	import { knowledgeBasesApi } from '$lib/api';
	import { toast } from '$lib/stores/toast';
	import type { ApiError } from '$lib/api';

	let name = $state('');
	let description = $state('');
	let seedContent = $state('');
	let isPublic = $state(false);
	let loading = $state(false);
	let error = $state('');

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';

		if (!name.trim()) {
			error = 'Name is required';
			return;
		}

		loading = true;

		try {
			const kb = await knowledgeBasesApi.create({
				name: name.trim(),
				description: description.trim() || undefined,
				is_public: isPublic,
				seed_content: seedContent.trim() || undefined
			});

			toast.success('Knowledge base created successfully!');
			goto(`/app/knowledge-bases/${kb.id}`);
		} catch (err) {
			const apiError = err as ApiError;
			error = apiError.message || 'Failed to create knowledge base';
			toast.error(error);
		} finally {
			loading = false;
		}
	}
</script>

<div class="animate-fade-in max-w-2xl mx-auto">
	<div class="mb-6">
		<a href="/app/knowledge-bases" class="text-sm text-gray-400 hover:text-gray-300">
			← Back to Knowledge Bases
		</a>
	</div>

	<h1 class="text-2xl font-bold text-gray-100 mb-6">Create Knowledge Base</h1>

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

			<div class="space-y-2">
				<label class="block text-sm font-medium text-gray-300">
					Seed Concept *
				</label>
				<p class="text-xs text-gray-500 mb-2">
					This is the starting point for your thought exploration. Enter an initial idea or concept.
				</p>
				<Textarea
					bind:value={seedContent}
					placeholder="e.g., Language shapes the way we think about reality"
					rows={4}
					maxlength={2000}
				/>
			</div>

			<div class="flex items-center justify-between p-4 bg-gray-700/30 rounded-lg">
				<div>
					<p class="font-medium text-gray-200">Make Public</p>
					<p class="text-sm text-gray-400">Allow others to view and copy this knowledge base</p>
				</div>
				<Toggle bind:checked={isPublic} />
			</div>

			{#if error}
				<p class="text-red-400 text-sm">{error}</p>
			{/if}

			<div class="flex items-center gap-4">
				<Button type="submit" {loading} class="flex-1">
					{loading ? 'Creating...' : 'Create Knowledge Base'}
				</Button>
				<a href="/app/knowledge-bases">
					<Button type="button" variant="ghost">Cancel</Button>
				</a>
			</div>
		</form>
	</Card>
</div>
