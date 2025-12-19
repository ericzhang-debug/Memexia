<script lang="ts">
	interface Props {
		label?: string;
		checked: boolean;
		onchange?: (checked: boolean) => void;
		disabled?: boolean;
		class?: string;
	}

	let {
		label,
		checked = $bindable(),
		onchange,
		disabled = false,
		class: className = ''
	}: Props = $props();

	function handleChange() {
		checked = !checked;
		onchange?.(checked);
	}
</script>

<label class="inline-flex items-center gap-3 cursor-pointer {disabled ? 'opacity-50' : ''} {className}">
	<button
		type="button"
		role="switch"
		aria-checked={checked}
		{disabled}
		onclick={handleChange}
		class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors
			{checked ? 'bg-cyan-500' : 'bg-gray-600'}"
	>
		<span
			class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform
				{checked ? 'translate-x-6' : 'translate-x-1'}"
		></span>
	</button>
	{#if label}
		<span class="text-sm text-gray-300">{label}</span>
	{/if}
</label>
