<script lang="ts">
	interface Props {
		page: number;
		totalPages: number;
		onchange: (page: number) => void;
		class?: string;
	}

	let { page, totalPages, onchange, class: className = '' }: Props = $props();

	function getPageNumbers(): (number | '...')[] {
		const pages: (number | '...')[] = [];
		const showEllipsisThreshold = 7;

		if (totalPages <= showEllipsisThreshold) {
			for (let i = 1; i <= totalPages; i++) {
				pages.push(i);
			}
		} else {
			pages.push(1);

			if (page > 3) {
				pages.push('...');
			}

			const start = Math.max(2, page - 1);
			const end = Math.min(totalPages - 1, page + 1);

			for (let i = start; i <= end; i++) {
				pages.push(i);
			}

			if (page < totalPages - 2) {
				pages.push('...');
			}

			pages.push(totalPages);
		}

		return pages;
	}
</script>

{#if totalPages > 1}
	<nav class="flex items-center gap-1 {className}" aria-label="Pagination">
		<button
			onclick={() => onchange(page - 1)}
			disabled={page <= 1}
			class="px-3 py-1.5 text-sm rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-700
				disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
			aria-label="Previous page"
		>
			&larr;
		</button>

		{#each getPageNumbers() as p}
			{#if p === '...'}
				<span class="px-2 text-gray-500">...</span>
			{:else}
				<button
					onclick={() => onchange(p)}
					class="px-3 py-1.5 text-sm rounded-lg transition-colors
						{p === page
						? 'bg-cyan-500 text-white'
						: 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'}"
					aria-current={p === page ? 'page' : undefined}
				>
					{p}
				</button>
			{/if}
		{/each}

		<button
			onclick={() => onchange(page + 1)}
			disabled={page >= totalPages}
			class="px-3 py-1.5 text-sm rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-700
				disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
			aria-label="Next page"
		>
			&rarr;
		</button>
	</nav>
{/if}
