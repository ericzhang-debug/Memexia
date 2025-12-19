<script lang="ts">
	import { goto } from '$app/navigation';
	import { Card, Button, Input } from '$lib/components/ui';
	import { authActions, isAuthenticated } from '$lib/stores';
	import { toast } from '$lib/stores/toast';
	import type { ApiError } from '$lib/api';

	let email = $state('');
	let username = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let loading = $state(false);
	let error = $state('');
	let success = $state(false);

	// Redirect if already authenticated
	$effect(() => {
		if ($isAuthenticated) {
			goto('/app/dashboard');
		}
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';

		// Validation
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		if (password.length < 6) {
			error = 'Password must be at least 6 characters';
			return;
		}

		loading = true;

		try {
			await authActions.register(email, username, password);
			success = true;
			toast.success('Registration successful! You can now login.');
		} catch (err) {
			const apiError = err as ApiError;
			error = apiError.message || 'Registration failed';
			toast.error(error);
		} finally {
			loading = false;
		}
	}
</script>

<Card>
	{#if success}
		<div class="text-center py-4">
			<div class="text-4xl mb-4">✓</div>
			<h2 class="text-xl font-semibold text-gray-100 mb-2">Registration Successful!</h2>
			<p class="text-gray-400 mb-4">
				Your account has been created. Please check your email to verify your account (if required).
			</p>
			<Button onclick={() => goto('/auth/login')}>
				Go to Login
			</Button>
		</div>
	{:else}
		<h2 class="text-xl font-semibold text-gray-100 mb-6">Create Account</h2>

		<form onsubmit={handleSubmit} class="space-y-4">
			<Input
				label="Email"
				type="email"
				bind:value={email}
				placeholder="you@example.com"
				required
				autocomplete="email"
			/>

			<Input
				label="Username"
				bind:value={username}
				placeholder="Choose a username"
				required
				minlength={3}
				maxlength={50}
				autocomplete="username"
			/>

			<Input
				label="Password"
				type="password"
				bind:value={password}
				placeholder="At least 6 characters"
				required
				minlength={6}
				autocomplete="new-password"
			/>

			<Input
				label="Confirm Password"
				type="password"
				bind:value={confirmPassword}
				placeholder="Confirm your password"
				required
				autocomplete="new-password"
			/>

			{#if error}
				<p class="text-red-400 text-sm">{error}</p>
			{/if}

			<Button type="submit" class="w-full" {loading}>
				{loading ? 'Creating account...' : 'Create Account'}
			</Button>
		</form>

		<p class="mt-6 text-center text-sm text-gray-400">
			Already have an account?
			<a href="/auth/login" class="text-cyan-400 hover:text-cyan-300">Sign in</a>
		</p>
	{/if}
</Card>
