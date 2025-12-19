<script lang="ts">
	import { onMount } from 'svelte';
	import { Card, Button, Loading, Dialog } from '$lib/components/ui';
	import { usersApi } from '$lib/api';
	import type { User, UserRoleUpdate } from '$lib/api';
	import { toast } from '$lib/stores/toast';
	import { user as currentUser } from '$lib/stores';

	let users = $state<User[]>([]);
	let loading = $state(true);

	// Dialog states
	let roleDialogOpen = $state(false);
	let selectedUser = $state<User | null>(null);
	let selectedRole = $state<'guest' | 'user' | 'admin'>('user');
	let roleLoading = $state(false);

	let deleteDialogOpen = $state(false);
	let deleteLoading = $state(false);

	async function loadUsers() {
		loading = true;
		try {
			users = await usersApi.list(0, 100);
		} catch (err) {
			toast.error('Failed to load users');
		} finally {
			loading = false;
		}
	}

	onMount(loadUsers);

	function openRoleDialog(user: User) {
		selectedUser = user;
		selectedRole = user.role as 'guest' | 'user' | 'admin';
		roleDialogOpen = true;
	}

	async function handleRoleUpdate() {
		if (!selectedUser) return;
		roleLoading = true;

		try {
			await usersApi.updateRole(selectedUser.id, { role: selectedRole });
			toast.success('Role updated');
			roleDialogOpen = false;
			await loadUsers();
		} catch (err) {
			toast.error('Failed to update role');
		} finally {
			roleLoading = false;
		}
	}

	function openDeleteDialog(user: User) {
		selectedUser = user;
		deleteDialogOpen = true;
	}

	async function handleDelete() {
		if (!selectedUser) return;
		deleteLoading = true;

		try {
			await usersApi.delete(selectedUser.id);
			toast.success('User deleted');
			deleteDialogOpen = false;
			await loadUsers();
		} catch (err) {
			toast.error('Failed to delete user');
		} finally {
			deleteLoading = false;
		}
	}

	async function toggleActive(user: User) {
		try {
			if (user.is_active) {
				await usersApi.deactivate(user.id);
				toast.success('User deactivated');
			} else {
				await usersApi.activate(user.id);
				toast.success('User activated');
			}
			await loadUsers();
		} catch (err) {
			toast.error('Failed to update user status');
		}
	}
</script>

<div class="animate-fade-in">
	<div class="flex items-center justify-between mb-6">
		<div>
			<h1 class="text-2xl font-bold text-gray-100">User Management</h1>
			<p class="text-gray-400 mt-1">Manage user accounts and permissions</p>
		</div>
	</div>

	{#if loading}
		<Loading size="lg" class="py-8" />
	{:else}
		<Card padding="sm">
			<div class="overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b border-gray-700">
							<th class="text-left py-3 px-4 text-sm font-medium text-gray-400">User</th>
							<th class="text-left py-3 px-4 text-sm font-medium text-gray-400">Role</th>
							<th class="text-left py-3 px-4 text-sm font-medium text-gray-400">Status</th>
							<th class="text-left py-3 px-4 text-sm font-medium text-gray-400">Created</th>
							<th class="text-right py-3 px-4 text-sm font-medium text-gray-400">Actions</th>
						</tr>
					</thead>
					<tbody>
						{#each users as user}
							<tr class="border-b border-gray-700/50 hover:bg-gray-700/20">
								<td class="py-3 px-4">
									<div>
										<p class="font-medium text-gray-100">{user.username}</p>
										<p class="text-sm text-gray-400">{user.email}</p>
									</div>
								</td>
								<td class="py-3 px-4">
									<div class="flex items-center gap-2">
										<span
											class="px-2 py-0.5 text-xs rounded capitalize
												{user.is_superuser
												? 'bg-purple-500/20 text-purple-400'
												: user.role === 'admin'
													? 'bg-cyan-500/20 text-cyan-400'
													: 'bg-gray-500/20 text-gray-400'}"
										>
											{user.is_superuser ? 'superuser' : user.role}
										</span>
									</div>
								</td>
								<td class="py-3 px-4">
									<div class="flex items-center gap-2">
										{#if user.is_active}
											<span class="w-2 h-2 rounded-full bg-green-400"></span>
											<span class="text-sm text-green-400">Active</span>
										{:else}
											<span class="w-2 h-2 rounded-full bg-red-400"></span>
											<span class="text-sm text-red-400">Inactive</span>
										{/if}
										{#if !user.is_verified}
											<span class="px-1.5 py-0.5 text-xs bg-yellow-500/20 text-yellow-400 rounded">
												Unverified
											</span>
										{/if}
									</div>
								</td>
								<td class="py-3 px-4 text-sm text-gray-400">
									{new Date(user.created_at).toLocaleDateString()}
								</td>
								<td class="py-3 px-4">
									<div class="flex items-center justify-end gap-2">
										{#if !user.is_superuser && user.id !== $currentUser?.id}
											<Button
												size="sm"
												variant="ghost"
												onclick={() => openRoleDialog(user)}
											>
												Role
											</Button>
											<Button
												size="sm"
												variant="ghost"
												onclick={() => toggleActive(user)}
											>
												{user.is_active ? 'Deactivate' : 'Activate'}
											</Button>
											<Button
												size="sm"
												variant="danger"
												onclick={() => openDeleteDialog(user)}
											>
												Delete
											</Button>
										{:else}
											<span class="text-xs text-gray-500">
												{user.is_superuser ? 'Protected' : 'You'}
											</span>
										{/if}
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</Card>
	{/if}
</div>

<!-- Role Update Dialog -->
<Dialog bind:open={roleDialogOpen} title="Update User Role">
	{#if selectedUser}
		<div class="space-y-4">
			<p class="text-gray-300">
				Change role for <strong>{selectedUser.username}</strong>
			</p>

			<div class="space-y-2">
				{#each ['guest', 'user', 'admin'] as role}
					<label class="flex items-center gap-3 p-3 bg-gray-700/30 rounded-lg cursor-pointer hover:bg-gray-700/50">
						<input
							type="radio"
							name="role"
							value={role}
							bind:group={selectedRole}
							class="w-4 h-4 text-cyan-500"
						/>
						<div>
							<p class="font-medium text-gray-100 capitalize">{role}</p>
							<p class="text-xs text-gray-400">
								{role === 'guest'
									? 'View-only access'
									: role === 'user'
										? 'Create and manage own content'
										: 'Full administrative access'}
							</p>
						</div>
					</label>
				{/each}
			</div>

			<div class="flex justify-end gap-3 pt-4">
				<Button variant="ghost" onclick={() => (roleDialogOpen = false)}>Cancel</Button>
				<Button onclick={handleRoleUpdate} loading={roleLoading}>
					{roleLoading ? 'Updating...' : 'Update Role'}
				</Button>
			</div>
		</div>
	{/if}
</Dialog>

<!-- Delete Confirmation Dialog -->
<Dialog bind:open={deleteDialogOpen} title="Delete User">
	{#if selectedUser}
		<p class="text-gray-300 mb-6">
			Are you sure you want to delete <strong>{selectedUser.username}</strong>? This will also
			delete all their knowledge bases and cannot be undone.
		</p>
		<div class="flex justify-end gap-3">
			<Button variant="ghost" onclick={() => (deleteDialogOpen = false)}>Cancel</Button>
			<Button variant="danger" onclick={handleDelete} loading={deleteLoading}>
				{deleteLoading ? 'Deleting...' : 'Delete User'}
			</Button>
		</div>
	{/if}
</Dialog>
