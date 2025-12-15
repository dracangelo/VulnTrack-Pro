// User Management Logic

async function fetchUsers() {
    try {
        const response = await fetch('/api/users/');
        if (!response.ok) throw new Error('Failed to fetch users');
        const users = await response.json();
        renderUsers(users);
    } catch (error) {
        console.error('Error fetching users:', error);
        // showNotification('Failed to load users', 'error');
    }
}

function renderUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td><span class="badge badge-${user.role === 'admin' ? 'danger' : 'info'}">${user.role || 'user'}</span></td>
            <td>
                <button class="btn btn-sm btn-secondary" onclick="editUser(${user.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function showCreateUserModal() {
    document.getElementById('userModalTitle').textContent = 'Create User';
    document.getElementById('userForm').reset();
    document.getElementById('userId').value = '';
    document.getElementById('userModal').classList.remove('hidden');
}

function closeUserModal() {
    document.getElementById('userModal').classList.add('hidden');
}

async function editUser(id) {
    try {
        const response = await fetch(`/api/users/${id}`);
        if (!response.ok) throw new Error('Failed to fetch user details');
        const user = await response.json();

        document.getElementById('userModalTitle').textContent = 'Edit User';
        document.getElementById('userId').value = user.id;
        document.getElementById('userUsername').value = user.username;
        document.getElementById('userEmail').value = user.email;
        document.getElementById('userRole').value = user.role || 'user';
        document.getElementById('userPassword').value = ''; // Don't show password

        document.getElementById('userModal').classList.remove('hidden');
    } catch (error) {
        console.error('Error fetching user:', error);
        UI.toast('Failed to load user details', 'error');
    }
}

async function saveUser(event) {
    event.preventDefault();

    const id = document.getElementById('userId').value;
    const username = document.getElementById('userUsername').value;
    const email = document.getElementById('userEmail').value;
    const role = document.getElementById('userRole').value;
    const password = document.getElementById('userPassword').value;

    const data = { username, email, role };
    if (password) data.password = password;

    const url = id ? `/api/users/${id}` : '/api/users/';
    const method = id ? 'PUT' : 'POST';

    await UI.asyncOperation(async () => {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            closeUserModal();
            fetchUsers();
            UI.toast('User saved successfully', 'success');
        } else {
            throw new Error(result.error || result.msg || result.message || 'Failed to save user');
        }
    }, 'Saving user...');
}

async function deleteUser(id) {
    if (!await UI.confirm('Are you sure you want to delete this user?')) return;

    await UI.asyncOperation(async () => {
        const response = await fetch(`/api/users/${id}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            fetchUsers();
            UI.toast('User deleted successfully', 'success');
        } else {
            const result = await response.json();
            throw new Error(result.error || result.msg || result.message || 'Failed to delete user');
        }
    }, 'Deleting user...');
}

// Invite Logic
function showInviteModal() {
    document.getElementById('inviteModal').classList.remove('hidden');
}

function closeInviteModal() {
    document.getElementById('inviteModal').classList.add('hidden');
    document.getElementById('inviteForm').reset();
}

async function sendInvite(event) {
    event.preventDefault();

    const email = document.getElementById('inviteEmail').value;
    const roleId = document.getElementById('inviteRole').value;

    await UI.asyncOperation(async () => {
        const response = await fetch('/api/auth/invite', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, role_id: parseInt(roleId) })
        });

        const result = await response.json();

        if (response.ok) {
            closeInviteModal();
            UI.toast('Invitation sent successfully', 'success');

            // If we got a token back (dev mode or just info), maybe log it or show it
            if (result.token) {
                console.log('Invite Token:', result.token);
                // In dev mode without SMTP, we might want to show this to the user
                // But for now, let's assume they check logs or it worked
            }
        } else {
            throw new Error(result.error || result.message || 'Failed to send invitation');
        }
    }, 'Sending invitation...');
}
