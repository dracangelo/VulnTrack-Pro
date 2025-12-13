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

            const formData = new FormData(e.target);
            const data = {
                name: formData.get('name'),
                description: formData.get('description')
            };

            await UI.asyncOperation(async () => {
                submitBtn.disabled = true;
                const response = await fetch('/api/teams/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    hideCreateTeamModal();
                    e.target.reset();
                    fetchTeams();
                    UI.toast('Team created successfully', 'success');
                } else {
                    const error = await response.json();
                    throw new Error(error.error || error.msg || error.message || 'Unknown error');
                }
            }, 'Creating team...').finally(() => {
                submitBtn.disabled = false;
            });
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
    const username = await UI.prompt("Enter username to add:", "text", "Username");
    if (!username) return;

    await UI.asyncOperation(async () => {
        const response = await fetch(`/api/teams/${teamId}/members`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username })
        });

        if (response.ok) {
            UI.toast('Member added successfully', 'success');
            showTeamDetails(teamId); // Refresh
        } else {
            const error = await response.json();
            throw new Error(error.error || error.message);
        }
    }, 'Adding member...');
};

// Remove Member
window.removeTeamMember = async function (teamId, userId) {
    if (!await UI.confirm('Are you sure you want to remove this member?')) return;

    await UI.asyncOperation(async () => {
        const response = await fetch(`/api/teams/${teamId}/members/${userId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showTeamDetails(teamId); // Refresh
            UI.toast('Member removed successfully', 'success');
        } else {
            throw new Error('Failed to remove member');
        }
    }, 'Removing member...');
};

// ========== Invitations ==========

window.showInviteModal = function () {
    document.getElementById('inviteModal').classList.remove('hidden');
    document.getElementById('inviteLinkInput').value = '';
};

window.hideInviteModal = function () {
    document.getElementById('inviteModal').classList.add('hidden');
};

window.generateInviteLink = async function () {
    const teamId = document.getElementById('currentTeamId').value;
    await UI.asyncOperation(async () => {
        const response = await fetch(`/api/teams/${teamId}/invites`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('inviteLinkInput').value = data.link;
            UI.toast('Invite link generated', 'success');
        } else {
            throw new Error('Failed to generate link');
        }
    }, 'Generating link...');
};

window.sendInviteEmail = async function (event) {
    event.preventDefault();
    const teamId = document.getElementById('currentTeamId').value;
    const email = document.getElementById('inviteEmailInput').value;

    await UI.asyncOperation(async () => {
        const response = await fetch(`/api/teams/${teamId}/invites`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: email })
        });

        if (response.ok) {
            UI.toast('Invitation sent successfully', 'success');
            document.getElementById('inviteEmailInput').value = '';
            hideInviteModal();
        } else {
            throw new Error('Failed to send invitation');
        }
    }, 'Sending invitation...');
};

// Check for invite in URL
window.checkInvite = async function () {
    const urlParams = new URLSearchParams(window.location.search);
    const inviteToken = urlParams.get('invite');

    if (inviteToken) {
        // Clear param
        window.history.replaceState({}, document.title, "/");

        if (!await UI.confirm('You have been invited to join a team. Do you want to join now?', 'Team Invitation')) return;

        await UI.asyncOperation(async () => {
            const response = await fetch(`/api/teams/invites/${inviteToken}/accept`, {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                UI.toast(data.message, 'success');
                fetchTeams(); // Refresh teams list
            } else {
                throw new Error(`Failed to join team: ${data.error || 'Unknown error'}`);
            }
        }, 'Joining team...');
    }
};
