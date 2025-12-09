// ========== Teams Management ==========

// Fetch and display teams
async function fetchTeams() {
    try {
        const response = await fetch('/api/teams/');
        const teams = await response.json();
        renderTeams(teams);
    } catch (error) {
        console.error('Error fetching teams:', error);
    }
}

// Render teams table
function renderTeams(teams) {
    const teamsList = document.getElementById('teamsTableBody');
    if (!teamsList) return;

    if (teams.length === 0) {
        teamsList.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                    No teams found. Create one to get started!
                </td>
            </tr>
        `;
        return;
    }

    teamsList.innerHTML = teams.map(team => `
        <tr>
            <td><strong>${team.name}</strong></td>
            <td>${team.description || '-'}</td>
            <td><span class="badge badge-info">${team.member_count} Members</span></td>
            <td>${new Date(team.created_at).toLocaleDateString()}</td>
            <td>
                <button onclick="showTeamDetails(${team.id})" class="btn btn-secondary" style="padding: 0.5rem 1rem;">
                    <i class="fas fa-users-cog"></i> Manage
                </button>
            </td>
        </tr>
    `).join('');
}

// Show Create Team Modal
window.showCreateTeamModal = function () {
    document.getElementById('createTeamModal').classList.remove('hidden');
};

window.hideCreateTeamModal = function () {
    document.getElementById('createTeamModal').classList.add('hidden');
};

// Handle Create Team Form Submit
document.addEventListener('DOMContentLoaded', () => {
    const createTeamForm = document.getElementById('createTeamForm');
    if (createTeamForm) {
        createTeamForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = createTeamForm.querySelector('button[type="submit"]');
            if (submitBtn.disabled) return;

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';

            const formData = new FormData(e.target);
            const data = {
                name: formData.get('name'),
                description: formData.get('description')
            };

            try {
                const response = await fetch('/api/teams/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    hideCreateTeamModal();
                    e.target.reset();
                    fetchTeams();
                    alert('Team created successfully!');
                } else {
                    const error = await response.json();
                    alert(`Failed to create team: ${error.error || error.msg || error.message || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error creating team:', error);
                alert('Failed to create team');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Team';
            }
        });
    }
});

// Show Team Details (Members)
window.showTeamDetails = async function (teamId) {
    // For now, we don't have a specific endpoint to get members of a team directly 
    // without fetching the team object which might not have full member details if not eager loaded.
    // However, the backend `get_teams` returns `member_count`. 
    // We might need a new endpoint or update `get_teams` to return members, 
    // OR we can use the `add_member` / `remove_member` endpoints.
    // Wait, let's check `Team.to_dict()` in `api/models/team.py`. 
    // It returns `member_count` but not the list of members.
    // We need to fetch members. Let's assume we might need to update the backend or 
    // use a separate call. 
    // Actually, looking at `api/routes/team_routes.py`, `get_teams` returns list of teams.
    // There isn't a specific `GET /api/teams/<id>` endpoint visible in the previous `view_file` of `team_routes.py`.
    // Let's double check `team_routes.py` content again.
    // It has `GET /`, `POST /`, `POST /<id>/members`, `DELETE /<id>/members/<user_id>`.
    // It seems we lack a `GET /<id>` to list members. 
    // I should probably add that to the backend plan if I want to list members.
    // BUT, I am in execution mode for frontend. 
    // Let's check if `get_teams` returns members. `Team.to_dict` only has `member_count`.
    // So I CANNOT list members with current backend.
    // I will add a TODO to update backend or just implement the UI for adding members blindly for now?
    // No, that's bad UX. 
    // I will implement a quick backend fix to add `GET /api/teams/<id>` or modify `to_dict`?
    // Modifying `to_dict` affects the list view performance.
    // I'll add `GET /api/teams/<int:team_id>` to `team_routes.py` quickly.

    // For now, let's just scaffold the modal.
    document.getElementById('teamDetailsModal').classList.remove('hidden');
    document.getElementById('currentTeamId').value = teamId;

    // Fetch team details (including members)
    try {
        const response = await fetch(`/api/teams/${teamId}`);
        if (response.ok) {
            const team = await response.json();
            document.getElementById('teamDetailsName').textContent = team.name;
            renderTeamMembers(team.members, teamId);
        } else {
            // Fallback if endpoint doesn't exist yet
            document.getElementById('teamDetailsName').textContent = 'Team ' + teamId;
            document.getElementById('teamMembersList').innerHTML = '<tr><td colspan="3">Unable to load members (Endpoint missing)</td></tr>';
        }
    } catch (error) {
        console.error('Error fetching team details:', error);
    }
};

window.hideTeamDetailsModal = function () {
    document.getElementById('teamDetailsModal').classList.add('hidden');
};

function renderTeamMembers(members, teamId) {
    const list = document.getElementById('teamMembersList');
    if (!members || members.length === 0) {
        list.innerHTML = '<tr><td colspan="3" class="text-center">No members yet</td></tr>';
        return;
    }

    list.innerHTML = members.map(member => `
        <tr>
            <td>${member.username}</td>
            <td>${member.email || '-'}</td>
            <td>
                <button onclick="removeTeamMember(${teamId}, ${member.id})" class="btn btn-xs btn-danger">
                    <i class="fas fa-times"></i> Remove
                </button>
            </td>
        </tr>
    `).join('');
}

// Add Member
window.addTeamMember = async function () {
    const teamId = document.getElementById('currentTeamId').value;
    const username = prompt("Enter username to add:");
    if (!username) return;

    try {
        const response = await fetch(`/api/teams/${teamId}/members`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username })
        });

        if (response.ok) {
            alert('Member added successfully');
            showTeamDetails(teamId); // Refresh
        } else {
            const error = await response.json();
            alert(`Failed to add member: ${error.error || error.message}`);
        }
    } catch (error) {
        console.error('Error adding member:', error);
        alert('Failed to add member');
    }
};

// Remove Member
window.removeTeamMember = async function (teamId, userId) {
    if (!confirm('Are you sure you want to remove this member?')) return;

    try {
        const response = await fetch(`/api/teams/${teamId}/members/${userId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showTeamDetails(teamId); // Refresh
        } else {
            alert('Failed to remove member');
        }
    } catch (error) {
        console.error('Error removing member:', error);
    }
};
