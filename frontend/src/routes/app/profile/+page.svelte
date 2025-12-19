<script lang="ts">
	import { Card, Button, Input } from '$lib/components/ui';
	import { user } from '$lib/stores';
	import { toast } from '$lib/stores/toast';

	// User data is read-only for now, editing would require backend support
</script>

<div class="animate-fade-in max-w-2xl">
	<h1 class="text-2xl font-bold text-gray-100 mb-6">Profile</h1>

	<Card>
		<div class="flex items-center gap-6 mb-8">
			<div class="w-20 h-20 bg-cyan-500/20 rounded-full flex items-center justify-center text-3xl text-cyan-400 font-bold">
				{$user?.username?.charAt(0).toUpperCase() || '?'}
			</div>
			<div>
				<h2 class="text-xl font-semibold text-gray-100">{$user?.username}</h2>
				<p class="text-gray-400">{$user?.email}</p>
				<div class="flex items-center gap-2 mt-2">
					<span class="px-2 py-1 text-xs bg-cyan-500/20 text-cyan-400 rounded capitalize">
						{$user?.role}
					</span>
					{#if $user?.is_superuser}
						<span class="px-2 py-1 text-xs bg-purple-500/20 text-purple-400 rounded">
							Superuser
						</span>
					{/if}
					{#if $user?.is_verified}
						<span class="px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded">
							Verified
						</span>
					{:else}
						<span class="px-2 py-1 text-xs bg-yellow-500/20 text-yellow-400 rounded">
							Not Verified
						</span>
					{/if}
				</div>
			</div>
		</div>

		<div class="space-y-4">
			<div>
				<label class="block text-sm font-medium text-gray-400 mb-1">User ID</label>
				<p class="text-gray-200">{$user?.id}</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-400 mb-1">Username</label>
				<p class="text-gray-200">{$user?.username}</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-400 mb-1">Email</label>
				<p class="text-gray-200">{$user?.email}</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-400 mb-1">Role</label>
				<p class="text-gray-200 capitalize">{$user?.role}</p>
			</div>

			<div>
				<label class="block text-sm font-medium text-gray-400 mb-1">Account Created</label>
				<p class="text-gray-200">
					{$user?.created_at ? new Date($user.created_at).toLocaleDateString() : 'Unknown'}
				</p>
			</div>
		</div>

		<div class="mt-8 pt-6 border-t border-gray-700">
			<h3 class="text-lg font-semibold text-gray-100 mb-4">Account Actions</h3>
			<div class="flex gap-4">
				<Button
					variant="secondary"
					onclick={() => toast.info('Password change feature coming soon!')}
				>
					Change Password
				</Button>
			</div>
		</div>
	</Card>
</div>
