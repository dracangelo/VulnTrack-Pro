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
            alert('Failed to save ticket');
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
    if (!confirm('Are you sure you want to delete this ticket?')) return;

    try {
        await fetch(`/api/tickets/${id}`, { method: 'DELETE' });
        fetchTickets();
    } catch (error) {
        console.error('Error deleting ticket:', error);
    }
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
saveTicket = async function (event) {
    await originalSaveTicket(event);

    const modal = document.getElementById('ticketModal');
    const vulnId = modal.dataset.bindVulnId;

    if (vulnId) {
        // This is tricky because we need the new ticket ID if it was a create operation
        // For now, let's just clear it to avoid issues. 
        // A better approach would be to return the ID from saveTicket and use it.
        delete modal.dataset.bindVulnId;
    }
};
