// Profile Management

async function fetchProfile() {
    try {
        // Fetch user info
        const userResponse = await fetch('/api/auth/me');
        if (userResponse.ok) {
            const user = await userResponse.json();
            renderProfile(user);
        } else {
            console.error('Failed to fetch profile');
        }

        // Fetch activity log
        const activityResponse = await fetch('/api/auth/activity');
        if (activityResponse.ok) {
            const activities = await activityResponse.json();
            renderActivityLog(activities);
        }
    } catch (error) {
        console.error('Error fetching profile data:', error);
    }
}

function renderProfile(user) {
    // Header Info
    document.getElementById('profileNameDisplay').textContent = user.username;
    document.getElementById('profileRoleDisplay').textContent = user.role || 'User';
    document.getElementById('profileAvatarLarge').textContent = user.username.charAt(0).toUpperCase();

    // Form Fields
    document.getElementById('editUsername').value = user.username;
    document.getElementById('editEmail').value = user.email || '';
    document.getElementById('readOnlyRole').value = user.role || 'User';
    // document.getElementById('readOnlyJoined').value = new Date(user.created_at).toLocaleDateString();
}

function renderActivityLog(activities) {
    const rows = activities.map(a => `
        <tr>
            <td>${formatAction(a.action)}</td>
            <td>${a.details || '-'}</td>
            <td style="color: var(--text-secondary); font-size: 0.85rem;">
                ${new Date(a.timestamp).toLocaleString()}
            </td>
        </tr>
    `).join('');

    // Render in both tabs
    const profileLog = document.getElementById('profileActivityLog');
    const notifLog = document.getElementById('notificationActivityLog');

    if (profileLog) profileLog.innerHTML = rows || '<tr><td colspan="3" class="text-center">No activity found</td></tr>';
    if (notifLog) notifLog.innerHTML = rows || '<tr><td colspan="3" class="text-center">No activity found</td></tr>';
}

function formatAction(action) {
    const map = {
        'successful_login': '<span class="badge badge-success">Login Success</span>',
        'failed_login': '<span class="badge badge-error">Login Failed</span>',
        'password_change': '<span class="badge badge-info">Password Changed</span>',
        'failed_password_change': '<span class="badge badge-warning">Password Change Failed</span>'
    };
    return map[action] || `<span class="badge">${action}</span>`;
}

function switchProfileTab(tabName) {
    // Update Sidebar
    const navItems = document.querySelectorAll('.profile-nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.getAttribute('onclick').includes(tabName)) {
            item.classList.add('active');
        }
    });

    // Show/Hide Content
    const tabs = ['info', 'settings', 'notifications'];
    tabs.forEach(t => {
        const el = document.getElementById(`profileTab-${t}`);
        if (t === tabName) {
            el.classList.remove('hidden');
        } else {
            el.classList.add('hidden');
        }
    });
}

async function updateProfileInfo(event) {
    event.preventDefault();

    const data = {
        username: document.getElementById('editUsername').value,
        email: document.getElementById('editEmail').value
    };

    try {
        const response = await fetch('/api/auth/me', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert('Profile updated successfully');
            fetchProfile(); // Refresh view
        } else {
            alert(`Failed to update profile: ${result.error || result.message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        alert('Failed to update profile');
    }
}

async function updatePassword(event) {
    event.preventDefault();

    const currentPassword = document.getElementById('currentPassword').value;
    const password = document.getElementById('editPassword').value;
    const confirm = document.getElementById('confirmPassword').value;

    if (password !== confirm) {
        alert('New passwords do not match');
        return;
    }

    if (password.length < 8) {
        alert('New password must be at least 8 characters');
        return;
    }

    try {
        const response = await fetch('/api/auth/me', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                password: password,
                current_password: currentPassword
            })
        });

        const result = await response.json();

        if (response.ok) {
            alert('Password updated successfully');
            document.getElementById('currentPassword').value = '';
            document.getElementById('editPassword').value = '';
            document.getElementById('confirmPassword').value = '';
            fetchProfile(); // Refresh logs
        } else {
            alert(`Failed to update password: ${result.error || result.message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error updating password:', error);
        alert('Failed to update password');
    }
}
