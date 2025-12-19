<script lang="ts">
	import { toast, type Toast } from '$lib/stores/toast';

	const typeStyles = {
		success: 'bg-green-600/90 border-green-500',
		error: 'bg-red-600/90 border-red-500',
		warning: 'bg-yellow-600/90 border-yellow-500',
		info: 'bg-cyan-600/90 border-cyan-500'
	};

	const typeIcons = {
		success: '✓',
		error: '✕',
		warning: '⚠',
		info: 'ℹ'
	};
</script>

<div class="fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
	{#each $toast as t (t.id)}
		<div
			class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg backdrop-blur-sm
				text-white text-sm font-medium animate-slide-in {typeStyles[t.type]}"
		>
			<span class="text-lg">{typeIcons[t.type]}</span>
			<span class="flex-1">{t.message}</span>
			<button
				onclick={() => toast.remove(t.id)}
				class="p-0.5 hover:bg-white/20 rounded transition-colors"
				aria-label="Dismiss"
			>
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				</svg>
			</button>
		</div>
	{/each}
</div>

<style>
	@keyframes slide-in {
		from {
			transform: translateX(100%);
			opacity: 0;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}

	.animate-slide-in {
		animation: slide-in 0.3s ease-out;
	}
</style>
