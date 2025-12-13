// Ticket Management

// Fetch and display tickets
async function fetchTickets() {
    try {
        const response = await fetch('/api/tickets/');
        const tickets = await response.json();
        renderTickets(tickets);
    } catch (error) {
        console.error('Error fetching tickets:', error);
    }
}

// Render tickets table
function renderTickets(tickets) {
    const tbody = document.getElementById('ticketList');
    if (!tbody) return;

    tbody.innerHTML = tickets.map(ticket => `
        <tr>
            <td>#${ticket.id}</td>
            <td><strong>${ticket.title}</strong></td>
            <td>${getPriorityBadge(ticket.priority)}</td>
            <td>${getStatusBadge(ticket.status)}</td>
            <td>${ticket.assignee_id ? `User ${ticket.assignee_id}` : 'Unassigned'}</td>
            <td>${ticket.vuln_count}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="editTicket(${ticket.id})">Edit</button>
                <button class="btn btn-danger btn-sm" onclick="deleteTicket(${ticket.id})">Delete</button>
            </td>
        </tr>
    `).join('');
}

function getPriorityBadge(priority) {
    const colors = {
        'high': 'badge-error',
        'medium': 'badge-warning',
        'low': 'badge-info'
    };
    return `<span class="badge ${colors[priority] || ''}">${priority}</span>`;
}

function getStatusBadge(status) {
    const colors = {
        'open': 'badge-error',
        'in_progress': 'badge-warning',
        'closed': 'badge-success'
    };
    return `<span class="badge ${colors[status] || ''}">${status.replace('_', ' ')}</span>`;
}

// Create Ticket Modal
function showCreateTicketModal() {
    document.getElementById('ticketModalTitle').textContent = 'Create Ticket';
    document.getElementById('ticketId').value = '';
    document.getElementById('ticketTitle').value = '';
    document.getElementById('ticketDescription').value = '';
    document.getElementById('ticketPriority').value = 'medium';
    document.getElementById('ticketStatus').value = 'open';
    document.getElementById('ticketAssignee').value = '';

    document.getElementById('ticketModal').classList.remove('hidden');
}

// Edit Ticket Modal
async function editTicket(id) {
    try {
        const response = await fetch(`/api/tickets/${id}`);
        const ticket = await response.json();

        document.getElementById('ticketModalTitle').textContent = 'Edit Ticket';
        document.getElementById('ticketId').value = ticket.id;
        document.getElementById('ticketTitle').value = ticket.title;
        document.getElementById('ticketDescription').value = ticket.description || '';
        document.getElementById('ticketPriority').value = ticket.priority;
        document.getElementById('ticketStatus').value = ticket.status;
        document.getElementById('ticketAssignee').value = ticket.assignee_id || '';

        document.getElementById('ticketModal').classList.remove('hidden');
    } catch (error) {
        console.error('Error fetching ticket details:', error);
    }
}

// Save Ticket (Create or Update)
async function saveTicket(event) {
    event.preventDefault();

    const id = document.getElementById('ticketId').value;
    const data = {
        title: document.getElementById('ticketTitle').value,
        description: document.getElementById('ticketDescription').value,
        priority: document.getElementById('ticketPriority').value,
        status: document.getElementById('ticketStatus').value,
        assignee_id: document.getElementById('ticketAssignee').value || null
    };

    const url = id ? `/api/tickets/${id}` : '/api/tickets/';
    const method = id ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            closeTicketModal();
            fetchTickets();
        } else {
            UI.toast('Failed to save ticket', 'error');
        }
    } catch (error) {
        console.error('Error saving ticket:', error);
    }
}

function closeTicketModal() {
    document.getElementById('ticketModal').classList.add('hidden');
}

// Delete Ticket
async function deleteTicket(id) {
    if (!await UI.confirm('Are you sure you want to delete this ticket?')) return;

    await UI.asyncOperation(async () => {
        await fetch(`/api/tickets/${id}`, { method: 'DELETE' });
        fetchTickets();
        UI.toast('Ticket deleted successfully', 'success');
    }, 'Deleting ticket...');
}

// Create Ticket from Vulnerability
function createTicketFromVuln(vulnId, vulnTitle) {
    showCreateTicketModal();
    document.getElementById('ticketTitle').value = `Fix: ${vulnTitle}`;
    document.getElementById('ticketDescription').value = `Remediation required for vulnerability #${vulnId}: ${vulnTitle}`;

    // We need to bind this vuln to the ticket after creation
    // For now, we'll just set a hidden field or handle it in the save function if we want to get fancy
    // But keeping it simple: User creates ticket, then we bind it.
    // Let's store the vulnId to bind later
    document.getElementById('ticketModal').dataset.bindVulnId = vulnId;
}

// Hook into saveTicket to handle binding if needed
const originalSaveTicket = saveTicket;
const modal = document.getElementById('ticketModal');
const vulnId = modal.dataset.bindVulnId;

if (vulnId) {
    // We need to wait for the save to complete and get the new ticket ID.
    // Since originalSaveTicket doesn't return the ID, we need to modify it or duplicate logic.
    // Let's rewrite saveTicket to handle this properly.
    // See below for the full rewrite of saveTicket.
}

// Redefining saveTicket to handle binding
// Redefining saveTicket to handle binding
saveTicket = async function (event) {
    event.preventDefault();

    const id = document.getElementById('ticketId').value;
    const data = {
        title: document.getElementById('ticketTitle').value,
        description: document.getElementById('ticketDescription').value,
        priority: document.getElementById('ticketPriority').value,
        status: document.getElementById('ticketStatus').value,
        assignee_id: document.getElementById('ticketAssignee').value || null
    };

    const url = id ? `/api/tickets/${id}` : '/api/tickets/';
    const method = id ? 'PUT' : 'POST';

    await UI.asyncOperation(async () => {
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const result = await response.json();
            const ticketId = id || result.id;

            // Handle Binding
            const modal = document.getElementById('ticketModal');
            const vulnId = modal.dataset.bindVulnId;

            if (vulnId && ticketId) {
                try {
                    await fetch(`/api/tickets/${ticketId}/bind`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ vuln_ids: [parseInt(vulnId)] })
                    });
                    console.log('Vulnerability bound to ticket');
                } catch (bindError) {
                    console.error('Error binding vulnerability:', bindError);
                    UI.toast('Ticket created but failed to bind vulnerability.', 'warning');
                }
                delete modal.dataset.bindVulnId;
            }

            closeTicketModal();
            fetchTickets();
            UI.toast('Ticket saved successfully', 'success');
        } else {
            throw new Error('Failed to save ticket');
        }
    }, 'Saving ticket...');
};
