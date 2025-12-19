<script lang="ts">
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/stores';
	import { Button, Card } from '$lib/components/ui';

	// Redirect authenticated users to dashboard
	$effect(() => {
		if ($isAuthenticated) {
			goto('/app/dashboard');
		}
	});
</script>

<div class="min-h-screen flex flex-col">
	<!-- Hero Section -->
	<div class="flex-1 flex items-center justify-center p-8">
		<div class="text-center max-w-3xl mx-auto">
			<h1 class="text-5xl font-bold text-white mb-4">
				<span class="text-cyan-400">Memexia</span>
			</h1>
			<p class="text-xl text-gray-300 mb-2">Autonomous Thought Universe</p>
			<p class="text-gray-400 mb-8 max-w-xl mx-auto">
				Let your ideas grow into new ideas. Build knowledge graphs that expand through AI-powered
				exploration and discover unexpected connections.
			</p>

			<div class="flex items-center justify-center gap-4">
				<a href="/auth/login">
					<Button size="lg">Sign In</Button>
				</a>
				<a href="/auth/register">
					<Button size="lg" variant="secondary">Create Account</Button>
				</a>
			</div>
		</div>
	</div>

	<!-- Features Section -->
	<div class="bg-gray-800/30 border-t border-gray-700 py-16 px-8">
		<div class="max-w-5xl mx-auto">
			<h2 class="text-2xl font-bold text-gray-100 text-center mb-12">How It Works</h2>

			<div class="grid grid-cols-1 md:grid-cols-3 gap-8">
				<Card class="text-center">
					<div class="text-4xl mb-4">🌱</div>
					<h3 class="text-lg font-semibold text-gray-100 mb-2">Plant a Seed</h3>
					<p class="text-gray-400 text-sm">
						Start with a concept, idea, or question. This becomes the seed of your knowledge universe.
					</p>
				</Card>

				<Card class="text-center">
					<div class="text-4xl mb-4">🧠</div>
					<h3 class="text-lg font-semibold text-gray-100 mb-2">AI Expansion</h3>
					<p class="text-gray-400 text-sm">
						Let AI explore related concepts, generate new ideas, and discover unexpected connections.
					</p>
				</Card>

				<Card class="text-center">
					<div class="text-4xl mb-4">🌐</div>
					<h3 class="text-lg font-semibold text-gray-100 mb-2">Explore in 3D</h3>
					<p class="text-gray-400 text-sm">
						Navigate your growing knowledge graph in an immersive 3D visualization.
					</p>
				</Card>
			</div>
		</div>
	</div>

	<!-- Footer -->
	<footer class="bg-gray-800/50 border-t border-gray-700 py-6 px-8">
		<div class="max-w-5xl mx-auto flex items-center justify-between text-sm text-gray-500">
			<p>
				&copy; 2024 Memexia. Licensed under <a href="https://www.gnu.org/licenses/agpl-3.0" class="text-gray-400 hover:text-gray-300">AGPL v3</a>.
			</p>
			<p>
				<a href="https://github.com/ChenXu233/Memexia" class="text-gray-400 hover:text-gray-300">GitHub</a>
			</p>
		</div>
	</footer>
</div>