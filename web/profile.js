// Profile Management

async function fetchProfile() {
    try {
        const response = await fetch('/api/auth/me');
        if (response.ok) {
            const user = await response.json();
            renderProfile(user);
        } else {
            console.error('Failed to fetch profile');
        }
    } catch (error) {
        console.error('Error fetching profile:', error);
    }
}

function renderProfile(user) {
    // View Mode
    document.getElementById('profileUsername').textContent = user.username;
    document.getElementById('profileEmail').textContent = user.email || 'Not set';
    document.getElementById('profileRole').textContent = user.role || 'User';
    document.getElementById('profileJoined').textContent = new Date(user.created_at).toLocaleDateString();

    // Edit Mode Inputs
    document.getElementById('editUsername').value = user.username;
    document.getElementById('editEmail').value = user.email || '';
}

function toggleEditProfile() {
    const viewMode = document.getElementById('profileViewMode');
    const editMode = document.getElementById('profileEditMode');

    if (viewMode.classList.contains('hidden')) {
        viewMode.classList.remove('hidden');
        editMode.classList.add('hidden');
    } else {
        viewMode.classList.add('hidden');
        editMode.classList.remove('hidden');
    }
}

async function updateProfile(event) {
    event.preventDefault();

    const data = {
        username: document.getElementById('editUsername').value,
        email: document.getElementById('editEmail').value
    };

    const password = document.getElementById('editPassword').value;
    if (password) {
        data.password = password;
    }

    try {
        const response = await fetch('/api/auth/me', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert('Profile updated successfully');
            document.getElementById('editPassword').value = ''; // Clear password
            toggleEditProfile();
            fetchProfile(); // Refresh view
        } else {
            alert(`Failed to update profile: ${result.error || result.message || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        alert('Failed to update profile');
    }
}
