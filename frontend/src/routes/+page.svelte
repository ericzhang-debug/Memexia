<script lang="ts">
import ThreeCanvas from '$lib/components/ThreeCanvas.svelte';

// UI state
let nodeCount = 600;
let nodeColor = '#00e5ff';
let speed = 1.0;
let animateOn = true;
</script>

<ThreeCanvas {nodeCount} {nodeColor} {speed} {animateOn} />

<div class="overlay">
	<h2>Scene Settings</h2>
	<label>Nodes: <input type="number" min="10" max="5000" bind:value={nodeCount} /></label>
	<label>Color: <input type="color" bind:value={nodeColor} /></label>
	<label>Speed: <input type="range" min="0" max="5" step="0.1" bind:value={speed} /> {speed}</label>
	<label><input type="checkbox" bind:checked={animateOn} /> Animate</label>
	<div class="hint">Tip: adjust nodes and speed for different effects</div>
</div>

<style>
	:global(html, body, #svelte) { height: 100%; }

	.overlay {
		position: fixed;
		right: 18px;
		top: 18px;
		z-index: 10;
		background: rgba(10,12,20,0.6);
		color: #e6f7ff;
		padding: 12px 16px;
		border-radius: 10px;
		backdrop-filter: blur(6px) saturate(1.1);
		box-shadow: 0 6px 20px rgba(0,0,0,0.5);
		width: 220px;
		font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
	}

	.overlay h2 { margin: 0 0 8px 0; font-size: 14px; }
	.overlay label { display: block; font-size: 13px; margin: 8px 0; }
	.overlay input[type="number"], .overlay input[type="color"], .overlay input[type="range"] { width: 100%; }
	.hint { font-size: 11px; opacity: 0.85; margin-top: 8px; }
</style>