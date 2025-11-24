document.addEventListener('DOMContentLoaded', () => {
    // Navigation handling
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = item.dataset.section;

            // Update active nav item
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Show corresponding section
            sections.forEach(section => section.classList.add('hidden'));
            document.getElementById(`${sectionId}-section`).classList.remove('hidden');
        });
    });

    // Modal handling
    window.showNewScanModal = () => {
        document.getElementById('newScanModal').classList.remove('hidden');
        populateScanTargets();
    };

    window.hideNewScanModal = () => {
        document.getElementById('newScanModal').classList.add('hidden');
    };

    function populateScanTargets() {
        fetch('/api/targets/')
            .then(res => res.json())
            .then(targets => {
                const select = document.getElementById('scanTargetSelect');
                select.innerHTML = '<option value="">Choose a target...</option>';
                targets.forEach(target => {
                    const option = document.createElement('option');
                    option.value = target.id;
                    option.textContent = `${target.name} (${target.ip_address})`;
                    select.appendChild(option);
                });
            });
    }

    // New Scan Form
    document.getElementById('newScanForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const targetId = formData.get('target_id');
        const scanType = formData.get('scan_type');

        const args = scanType === 'nmap_full' ? '-sV -T4' : '-F';

        try {
            const response = await fetch('/api/scans/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_id: parseInt(targetId),
                    scan_type: 'nmap',
                    args: args
                })
            });

            if (response.ok) {
                hideNewScanModal();
                alert('Scan started successfully!');
                fetchScans();
            } else {
                alert('Failed to start scan');
            }
        } catch (error) {
            console.error('Error starting scan:', error);
        }
    });

    // Fetch and display targets
    async function fetchTargets() {
        try {
            const response = await fetch('/api/targets/');
            const targets = await response.json();
            renderTargets(targets);
        } catch (error) {
            console.error('Error fetching targets:', error);
        }
    }

    function renderTargets(targets) {
        const targetList = document.getElementById('targetList');
        if (!targetList) return;

        targetList.innerHTML = targets.map(target => `
            <tr>
                <td>${target.name || 'Unnamed'}</td>
                <td><span class="badge badge-cyan">${target.ip_address}</span></td>
                <td>${target.description || '-'}</td>
                <td>
                    <button onclick="startScan(${target.id})" class="btn btn-primary" style="padding: 0.5rem 1rem; margin-right: 0.5rem;">
                        <i class="fas fa-radar"></i> Scan
                    </button>
                    <button onclick="deleteTarget(${target.id})" class="btn btn-danger" style="padding: 0.5rem 1rem;">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // Add new target
    const addTargetForm = document.getElementById('addTargetForm');
    if (addTargetForm) {
        addTargetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                name: formData.get('name') || formData.get('ip_address'),
                ip_address: formData.get('ip_address'),
                description: formData.get('description')
            };

            try {
                const response = await fetch('/api/targets/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    e.target.reset();
                    fetchTargets();
                    alert('Target added successfully!');
                } else {
                    alert('Failed to add target');
                }
            } catch (error) {
                console.error('Error adding target:', error);
            }
        });
    }

    // Delete target
    window.deleteTarget = async (id) => {
        if (!confirm('Are you sure you want to delete this target?')) return;

        try {
            const response = await fetch(`/api/targets/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchTargets();
                alert('Target deleted successfully!');
            } else {
                alert('Failed to delete target');
            }
        } catch (error) {
            console.error('Error deleting target:', error);
        }
    };

    // Fetch and display scans
    async function fetchScans() {
        try {
            const response = await fetch('/api/scans/');
            const scans = await response.json();
            renderScans(scans);
        } catch (error) {
            console.error('Error fetching scans:', error);
        }
    }

    function renderScans(scans) {
        const scanList = document.getElementById('scanList');
        if (!scanList) return;

        scanList.innerHTML = scans.map(scan => `
            <tr>
                <td><span class="badge badge-info">#${scan.id}</span></td>
                <td>${scan.target_name || 'Unknown'}</td>
                <td>${scan.scan_type}</td>
                <td>${getScanStatusBadge(scan.status)}</td>
                <td>${new Date(scan.created_at).toLocaleString()}</td>
                <td>
                    ${scan.status === 'completed' ?
                `<button onclick="downloadReport(${scan.id}, 'html')" class="btn btn-secondary" style="padding: 0.5rem 1rem; margin-right: 0.5rem;">
                            <i class="fas fa-file-code"></i> HTML
                        </button>
                        <button onclick="downloadReport(${scan.id}, 'pdf')" class="btn btn-secondary" style="padding: 0.5rem 1rem;">
                            <i class="fas fa-file-pdf"></i> PDF
                        </button>`
                : '<span style="color: var(--text-muted);">-</span>'}
                </td>
            </tr>
        `).join('');
    }

    function getScanStatusBadge(status) {
        const badges = {
            'completed': '<span class="badge badge-success">Completed</span>',
            'running': '<span class="badge badge-info">Running</span>',
            'failed': '<span class="badge badge-error">Failed</span>',
            'pending': '<span class="badge badge-warning">Pending</span>'
        };
        return badges[status] || `<span class="badge">${status}</span>`;
    }

    window.startScan = async (targetId) => {
        if (!confirm('Start Nmap scan for this target?')) return;

        try {
            const response = await fetch('/api/scans/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_id: targetId,
                    scan_type: 'nmap',
                    args: '-F'
                })
            });

            if (response.ok) {
                alert('Scan started!');
                fetchScans();
            } else {
                alert('Failed to start scan');
            }
        } catch (error) {
            console.error('Error starting scan:', error);
        }
    };

    window.downloadReport = (scanId, format) => {
        window.location.href = `/api/reports/${scanId}/download?format=${format}`;
    };

    // Dashboard - Fetch stats
    async function fetchStats() {
        try {
            const response = await fetch('/api/reports/stats');
            const data = await response.json();
            renderDashboard(data);
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }

    function renderDashboard(data) {
        // Severity Chart
        const ctx = document.getElementById('severityChart');
        if (!ctx) return;

        const severityOrder = ['Critical', 'High', 'Medium', 'Low', 'Info'];
        const counts = severityOrder.map(sev => data.severity_counts[sev] || 0);

        new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: severityOrder,
                datasets: [{
                    data: counts,
                    backgroundColor: [
                        '#EF4444', // Critical
                        '#F59E0B', // High
                        '#EAB308', // Medium
                        '#10B981', // Low
                        '#3B82F6'  // Info
                    ],
                    borderColor: '#1A2332',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#9CA3AF',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });

        // Top Hosts
        const topHostsList = document.getElementById('topHostsList');
        if (topHostsList) {
            topHostsList.innerHTML = data.top_vulnerable_hosts.map(host => `
                <li style="padding: 0.75rem 0; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between;">
                    <span style="color: var(--text-primary);">${host.name}</span>
                    <span class="badge badge-error">${host.count} vulnerabilities</span>
                </li>
            `).join('');
        }
    }

    // Fetch tickets
    async function fetchTickets() {
        try {
            const response = await fetch('/api/tickets/');
            const tickets = await response.json();
            renderTickets(tickets);
        } catch (error) {
            console.error('Error fetching tickets:', error);
        }
    }

    function renderTickets(tickets) {
        const ticketList = document.getElementById('ticketList');
        if (!ticketList) return;

        ticketList.innerHTML = tickets.map(ticket => `
            <tr>
                <td><span class="badge badge-info">#${ticket.id}</span></td>
                <td>${ticket.title}</td>
                <td>${getStatusBadge(ticket.status)}</td>
                <td>${getPriorityBadge(ticket.priority)}</td>
                <td>${ticket.vuln_count || 0}</td>
            </tr>
        `).join('');
    }

    function getStatusBadge(status) {
        const badges = {
            'open': '<span class="badge badge-success">Open</span>',
            'in_progress': '<span class="badge badge-warning">In Progress</span>',
            'closed': '<span class="badge">Closed</span>'
        };
        return badges[status] || `<span class="badge">${status}</span>`;
    }

    function getPriorityBadge(priority) {
        const badges = {
            'critical': '<span class="badge badge-error">Critical</span>',
            'high': '<span class="badge badge-warning">High</span>',
            'medium': '<span class="badge badge-info">Medium</span>',
            'low': '<span class="badge">Low</span>'
        };
        return badges[priority] || `<span class="badge">${priority}</span>`;
    }

    // Initial data fetch
    fetchTargets();
    fetchScans();
    fetchStats();
    fetchTickets();

    // Auto-refresh scans every 10 seconds
    setInterval(fetchScans, 10000);
});
