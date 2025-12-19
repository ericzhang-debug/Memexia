<script lang="ts">
	import { page } from '$app/stores';
	import { Card, Button, Input } from '$lib/components/ui';
	import { authApi } from '$lib/api';
	import { toast } from '$lib/stores/toast';
	import type { ApiError } from '$lib/api';

	// Check for reset token in URL
	let resetToken = $derived($page.url.searchParams.get('token'));

	// Request password reset form state
	let email = $state('');
	let requestLoading = $state(false);
	let requestSent = $state(false);

	// Reset password form state
	let newPassword = $state('');
	let confirmPassword = $state('');
	let resetLoading = $state(false);
	let resetSuccess = $state(false);
	let error = $state('');

	async function handleRequestReset(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		requestLoading = true;

		try {
			await authApi.forgotPassword({ email });
			requestSent = true;
			toast.success('Password reset email sent!');
		} catch (err) {
			const apiError = err as ApiError;
			// Don't reveal if email exists
			requestSent = true;
			toast.info('If an account exists with this email, a reset link has been sent.');
		} finally {
			requestLoading = false;
		}
	}

	async function handleResetPassword(e: SubmitEvent) {
		e.preventDefault();
		error = '';

		if (newPassword !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		if (newPassword.length < 6) {
			error = 'Password must be at least 6 characters';
			return;
		}

		if (!resetToken) {
			error = 'Invalid reset token';
			return;
		}

		resetLoading = true;

		try {
			await authApi.resetPassword({
				token: resetToken,
				new_password: newPassword
			});
			resetSuccess = true;
			toast.success('Password reset successfully!');
		} catch (err) {
			const apiError = err as ApiError;
			error = apiError.message || 'Failed to reset password';
			toast.error(error);
		} finally {
			resetLoading = false;
		}
	}
</script>

<Card>
	{#if resetToken}
		<!-- Reset Password Form -->
		{#if resetSuccess}
			<div class="text-center py-4">
				<div class="text-4xl mb-4">✓</div>
				<h2 class="text-xl font-semibold text-gray-100 mb-2">Password Reset!</h2>
				<p class="text-gray-400 mb-4">
					Your password has been successfully reset.
				</p>
				<a href="/auth/login">
					<Button>Go to Login</Button>
				</a>
			</div>
		{:else}
			<h2 class="text-xl font-semibold text-gray-100 mb-6">Reset Password</h2>

			<form onsubmit={handleResetPassword} class="space-y-4">
				<Input
					label="New Password"
					type="password"
					bind:value={newPassword}
					placeholder="Enter new password"
					required
					minlength={6}
					autocomplete="new-password"
				/>

				<Input
					label="Confirm New Password"
					type="password"
					bind:value={confirmPassword}
					placeholder="Confirm new password"
					required
					autocomplete="new-password"
				/>

				{#if error}
					<p class="text-red-400 text-sm">{error}</p>
				{/if}

				<Button type="submit" class="w-full" loading={resetLoading}>
					{resetLoading ? 'Resetting...' : 'Reset Password'}
				</Button>
			</form>
		{/if}
	{:else}
		<!-- Request Password Reset Form -->
		{#if requestSent}
			<div class="text-center py-4">
				<div class="text-4xl mb-4">✉️</div>
				<h2 class="text-xl font-semibold text-gray-100 mb-2">Check Your Email</h2>
				<p class="text-gray-400 mb-4">
					If an account exists with the email you provided, we've sent a password reset link.
				</p>
				<a href="/auth/login">
					<Button variant="secondary">Back to Login</Button>
				</a>
			</div>
		{:else}
			<h2 class="text-xl font-semibold text-gray-100 mb-6">Forgot Password</h2>
			<p class="text-gray-400 text-sm mb-6">
				Enter your email address and we'll send you a link to reset your password.
			</p>

			<form onsubmit={handleRequestReset} class="space-y-4">
				<Input
					label="Email"
					type="email"
					bind:value={email}
					placeholder="you@example.com"
					required
					autocomplete="email"
				/>

				<Button type="submit" class="w-full" loading={requestLoading}>
					{requestLoading ? 'Sending...' : 'Send Reset Link'}
				</Button>
			</form>

			<p class="mt-6 text-center text-sm text-gray-400">
				Remember your password?
				<a href="/auth/login" class="text-cyan-400 hover:text-cyan-300">Sign in</a>
			</p>
		{/if}
	{/if}
</Card>
