document.addEventListener('DOMContentLoaded', () => {
    // Navigation handling
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');

    function showSection(sectionId, clickedNavItem = null) {
        // Hide all sections
        sections.forEach(section => {
            section.classList.add('hidden');
        });

        // Show selected section
        document.getElementById(`${sectionId}-section`).classList.remove('hidden');

        // Update active nav item
        navItems.forEach(item => {
            item.classList.remove('active');
        });
        if (clickedNavItem) {
            clickedNavItem.classList.add('active');
        } else {
            // If not clicked, find the nav item by sectionId and activate it
            const correspondingNavItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
            if (correspondingNavItem) {
                correspondingNavItem.classList.add('active');
            }
        }

        // Stop queue refresh when leaving scans section
        stopQueueRefresh();

        // Start queue refresh if on scans section
        if (sectionId === 'scans') { // Changed from 'scansSection' to 'scans' to match data-section attribute
            startQueueRefresh();
        }

        // Load data for the section
        if (sectionId === 'dashboard') { // Changed from 'dashboardSection' to 'dashboard'
            // fetchStats(); // Assuming this function exists elsewhere
        } else if (sectionId === 'targets') { // Changed from 'targetsSection' to 'targets'
            fetchTargets();
        } else if (sectionId === 'scans') { // Changed from 'scansSection' to 'scans'
            // fetchScans(); // Assuming this function exists elsewhere
        } else if (sectionId === 'tickets') { // Changed from 'ticketsSection' to 'tickets'
            // fetchTickets(); // Assuming this function exists elsewhere
        } else if (sectionId === 'vulnerabilities') { // Changed from 'vulnerabilitiesSection' to 'vulnerabilities'
            // fetchVulnerabilities(); // Assuming this function exists elsewhere
        }
    }

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = item.dataset.section;
            showSection(sectionId, item);
        });
    });

    // Set initial active section (e.g., dashboard)
    // This part is important to ensure a section is shown on load and queue refresh starts if on scans
    const initialSectionId = 'dashboard'; // Or whatever your default section is
    showSection(initialSectionId);


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
                const result = await response.json();
                hideNewScanModal();

                // Get target name
                const targetSelect = document.getElementById('scanTargetSelect');
                const targetName = targetSelect.options[targetSelect.selectedIndex].text;

                // Show live scan progress
                showLiveScan(result.scan_id, targetName);
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

    // Queue Status Management
    async function refreshQueueStatus() {
        try {
            const response = await fetch('/api/scans/queue/status');
            const data = await response.json();

            // Update counts
            document.getElementById('activeScanCount').textContent = data.active_count;
            document.getElementById('maxConcurrent').textContent = data.max_concurrent;
            document.getElementById('queueSize').textContent = data.queue_size;

            // Render active scans
            const activeContainer = document.getElementById('activeScansContainer');
            if (data.active_scans.length === 0) {
                activeContainer.innerHTML = '<p style="color: var(--text-secondary); padding: 1rem;">No active scans</p>';
            } else {
                activeContainer.innerHTML = data.active_scans.map(scan => `
                    <div style="padding: 1rem; border-bottom: 1px solid var(--border-color);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <div>
                                <strong style="color: var(--accent-cyan);">${scan.target_name}</strong>
                                <span style="color: var(--text-secondary); margin-left: 0.5rem;">${scan.scan_type}</span>
                            </div>
                            <span class="badge badge-${scan.status}">${scan.status}</span>
                        </div>
                        <div class="progress-bar" style="height: 8px;">
                            <div class="progress-fill" style="width: ${scan.progress}%;"></div>
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">
                            ${scan.progress}% complete
                        </div>
                    </div>
                `).join('');
            }

            // Render queued scans
            const queueContainer = document.getElementById('queuedScansContainer');
            if (data.queued_scans.length === 0) {
                queueContainer.innerHTML = '<p style="color: var(--text-secondary); padding: 1rem;">No queued scans</p>';
            } else {
                queueContainer.innerHTML = data.queued_scans.map(scan => `
                    <div style="padding: 1rem; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: var(--text-primary);">${scan.target_name}</strong>
                            <span style="color: var(--text-secondary); margin-left: 0.5rem;">${scan.scan_type}</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <span style="color: var(--text-secondary); font-size: 0.875rem;">Position: ${scan.queue_position}</span>
                            <span class="badge badge-queued">queued</span>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error fetching queue status:', error);
        }
    }

    // Auto-refresh queue status every 5 seconds when on scans page
    let queueRefreshInterval = null;

    function startQueueRefresh() {
        refreshQueueStatus();
        queueRefreshInterval = setInterval(refreshQueueStatus, 5000);
    }

    function stopQueueRefresh() {
        if (queueRefreshInterval) {
            clearInterval(queueRefreshInterval);
            queueRefreshInterval = null;
        }
    }

    // Live Scan Progress Tracking with WebSockets
    let progressPollInterval = null;
    let currentScanId = null;
    let socket = null;

    // Initialize WebSocket connection
    function initWebSocket() {
        if (!socket) {
            socket = io('/scan-progress', {
                transports: ['websocket', 'polling']
            });

            socket.on('connected', (data) => {
                console.log('WebSocket connected:', data);
            });

            socket.on('progress_update', (data) => {
                if (data.id === currentScanId) {
                    updateProgressUI(data);
                }
            });

            socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
            });
        }
    }

    window.showLiveScan = (scanId, targetName) => {
        currentScanId = scanId;
        document.getElementById('liveScanModal').classList.remove('hidden');
        document.getElementById('liveScanTarget').textContent = `Target: ${targetName}`;

        // Initialize WebSocket and subscribe to scan
        initWebSocket();
        socket.emit('subscribe_scan', { scan_id: scanId });

        // Also poll initially for immediate update
        updateProgress(scanId);
    };

    window.closeLiveScan = () => {
        document.getElementById('liveScanModal').classList.add('hidden');

        // Unsubscribe from WebSocket
        if (socket && currentScanId) {
            socket.emit('unsubscribe_scan', { scan_id: currentScanId });
        }

        stopProgressPolling();
        fetchScans(); // Refresh scan list
    };

    function startProgressPolling(scanId) {
        // Clear any existing interval
        stopProgressPolling();

        // Poll immediately
        updateProgress(scanId);

        // Then poll every 5 seconds as fallback (WebSocket is primary)
        progressPollInterval = setInterval(() => {
            updateProgress(scanId);
        }, 5000);
    }

    function stopProgressPolling() {
        if (progressPollInterval) {
            clearInterval(progressPollInterval);
            progressPollInterval = null;
        }
    }

    async function updateProgress(scanId) {
        try {
            const response = await fetch(`/api/scans/${scanId}/progress`);
            const data = await response.json();
            updateProgressUI(data);
        } catch (error) {
            console.error('Error fetching progress:', error);
        }
    }

    function updateProgressUI(data) {
        // Update UI
        document.getElementById('progressPercentage').textContent = `${data.progress}%`;
        document.getElementById('progressFill').style.width = `${data.progress}%`;
        document.getElementById('currentStep').textContent = data.current_step;

        // Update ETA
        if (data.eta_seconds) {
            const minutes = Math.floor(data.eta_seconds / 60);
            const seconds = data.eta_seconds % 60;
            document.getElementById('etaDisplay').textContent = `${minutes}m ${seconds}s`;
        } else {
            document.getElementById('etaDisplay').textContent = 'Calculating...';
        }

        // Update elapsed time
        if (data.elapsed_seconds) {
            const minutes = Math.floor(data.elapsed_seconds / 60);
            const seconds = data.elapsed_seconds % 60;
            document.getElementById('elapsedDisplay').textContent = `${minutes}m ${seconds}s`;
        }

        // Add log entry
        addLogEntry(data.current_step, 'INFO');

        // Update vulnerability counts
        document.getElementById('vulnTotal').textContent = data.vuln_count || 0;
        if (data.vuln_breakdown) {
            document.getElementById('vulnCritical').textContent = data.vuln_breakdown.Critical || 0;
            document.getElementById('vulnHigh').textContent = data.vuln_breakdown.High || 0;
            document.getElementById('vulnMedium').textContent = data.vuln_breakdown.Medium || 0;
        }

        // Check if scan is complete
        if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
            stopProgressPolling();
            setTimeout(() => {
                closeLiveScan();
            }, 2000); // Close after 2 seconds
        }
    }

    function addLogEntry(message, level = 'INFO') {
        const logContainer = document.getElementById('liveLog');
        const now = new Date();
        const timestamp = now.toTimeString().split(' ')[0];

        const logLine = document.createElement('div');
        logLine.className = 'log-line';
        logLine.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span>
            <span class="log-level-${level}">[${level}]</span>
            <span>${message}</span>
        `;

        logContainer.appendChild(logLine);
        logContainer.scrollTop = logContainer.scrollHeight;

        // Keep only last 50 entries
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    window.cancelScan = async () => {
        if (!confirm('Are you sure you want to cancel this scan?')) return;

        try {
            const response = await fetch(`/api/scans/${currentScanId}/cancel`, {
                method: 'DELETE'
            });

            if (response.ok) {
                addLogEntry('Scan cancellation requested', 'WARN');
                stopProgressPolling();
                setTimeout(() => {
                    closeLiveScan();
                }, 1000);
            } else {
                const error = await response.json();
                alert(`Failed to cancel scan: ${error.error}`);
            }
        } catch (error) {
            console.error('Error cancelling scan:', error);
            alert('Failed to cancel scan');
        }
    };

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
                const result = await response.json();

                // Get target name from the table
                const targetRow = event.target.closest('tr');
                const targetName = targetRow.querySelector('td:first-child').textContent;

                // Show live scan progress
                showLiveScan(result.scan_id, targetName);
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
