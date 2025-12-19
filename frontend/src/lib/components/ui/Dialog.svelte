<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		open: boolean;
		onclose?: () => void;
		title?: string;
		class?: string;
		children?: Snippet;
	}

	let { open = $bindable(), onclose, title, class: className = '', children }: Props = $props();

	function handleBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			close();
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			close();
		}
	}

	function close() {
		open = false;
		onclose?.();
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
		role="dialog"
		aria-modal="true"
		onclick={handleBackdropClick}
		onkeydown={handleKeydown}
	>
		<div
			class="relative w-full max-w-lg bg-gray-800 border border-gray-700 rounded-xl shadow-2xl {className}"
		>
			{#if title}
				<div class="flex items-center justify-between px-6 py-4 border-b border-gray-700">
					<h2 class="text-lg font-semibold text-gray-100">{title}</h2>
					<button
						onclick={close}
						class="p-1 text-gray-400 hover:text-gray-200 transition-colors"
						aria-label="Close"
					>
						<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				</div>
			{/if}
			<div class="p-6">
				{@render children?.()}
			</div>
		</div>
	</div>
{/if}
