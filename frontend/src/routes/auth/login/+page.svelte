<script lang="ts">
	import { goto } from '$app/navigation';
	import { Card, Button, Input } from '$lib/components/ui';
	import { authActions, isAuthenticated } from '$lib/stores';
	import { toast } from '$lib/stores/toast';
	import type { ApiError } from '$lib/api';

	let username = $state('');
	let password = $state('');
	let loading = $state(false);
	let error = $state('');

	// Redirect if already authenticated
	$effect(() => {
		if ($isAuthenticated) {
			goto('/app/dashboard');
		}
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;

		try {
			await authActions.login(username, password);
			toast.success('Login successful!');
			goto('/app/dashboard');
		} catch (err) {
			const apiError = err as ApiError;
			error = apiError.message || 'Login failed';
			toast.error(error);
		} finally {
			loading = false;
		}
	}
</script>

<Card>
	<h2 class="text-xl font-semibold text-gray-100 mb-6">Sign In</h2>

	<form onsubmit={handleSubmit} class="space-y-4">
		<Input
			label="Username"
			bind:value={username}
			placeholder="Enter your username"
			required
			autocomplete="username"
		/>

		<Input
			label="Password"
			type="password"
			bind:value={password}
			placeholder="Enter your password"
			required
			autocomplete="current-password"
		/>

		{#if error}
			<p class="text-red-400 text-sm">{error}</p>
		{/if}

		<Button type="submit" class="w-full" {loading}>
			{loading ? 'Signing in...' : 'Sign In'}
		</Button>
	</form>

	<div class="mt-6 space-y-2 text-center text-sm">
		<p class="text-gray-400">
			Don't have an account?
			<a href="/auth/register" class="text-cyan-400 hover:text-cyan-300">Register</a>
		</p>
		<p>
			<a href="/auth/forgot-password" class="text-gray-400 hover:text-gray-300">Forgot password?</a>
		</p>
	</div>
</Card>
