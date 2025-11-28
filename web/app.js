document.addEventListener('DOMContentLoaded', () => {
    // Variable declarations - must be at top to avoid hoisting issues
    let queueRefreshInterval = null;
    let progressPollInterval = null;
    let currentScanId = null;
    let socket = null;
    let hostsDiscoveredCount = 0;
    let portsDiscoveredCount = 0;
    let openvasConfigs = [];

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
        if (sectionId === 'dashboard') {
            // fetchStats(); // Assuming this function exists elsewhere
        } else if (sectionId === 'targets') {
            fetchTargets();
        } else if (sectionId === 'scans') {
            fetchScans(); // Fetch scans when viewing scans section
            refreshQueueStatus(); // Also refresh queue status
        } else if (sectionId === 'tickets') {
            fetchTickets();
        } else if (sectionId === 'vulnerabilities') {
            populateVulnTargets(); // Populate target dropdown
        } else if (sectionId === 'reports') {
            fetchReports();
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

    // Tab switching for target management
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            tab.classList.add('active');

            const tabType = tab.dataset.tab;
            // For now, just show a message for range/cidr and hostname tabs
            // These would need backend support for full implementation
            if (tabType === 'range' || tabType === 'hostname') {
                alert(`${tabType.toUpperCase()} target addition coming soon! For now, please use Single Target.`);
                // Switch back to single tab
                document.querySelector('.tab[data-tab="single"]').classList.add('active');
                tab.classList.remove('active');
            }
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

        const requestData = {
            target_id: parseInt(targetId)
        };

        if (scanType === 'openvas') {
            requestData.scan_type = 'openvas';
            const configId = formData.get('openvas_config_id');
            if (configId) {
                requestData.openvas_config_id = configId;
            }
        } else {
            requestData.scan_type = 'nmap';
            requestData.args = scanType === 'nmap_full' ? '-sV -T4' : '-F';
        }

        try {
            const response = await fetch('/api/scans/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
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
    window.refreshQueueStatus = async function refreshQueueStatus() {
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
        const scanList = document.getElementById('scansList'); // Changed from scanList to scansList
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
                        <button onclick="downloadReport(${scan.id}, 'pdf')" class="btn btn-secondary" style="padding: 0.5rem 1rem; margin-right: 0.5rem;">
                            <i class="fas fa-file-pdf"></i> PDF
                        </button>`
                : '<span style="color: var(--text-muted);">-</span>'}
                    ${scan.status !== 'running' ?
                `<button onclick="deleteScan(${scan.id})" class="btn btn-danger" style="padding: 0.5rem 1rem;">
                            <i class="fas fa-trash"></i>
                        </button>`
                : ''}
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

                // Get target name by fetching targets
                const targetsResponse = await fetch('/api/targets/');
                const targets = await targetsResponse.json();
                const target = targets.find(t => t.id === targetId);
                const targetName = target ? target.name : 'Unknown Target';

                // Show live scan progress
                showLiveScan(result.scan_id, targetName);
            } else {
                alert('Failed to start scan');
            }
        } catch (error) {
            console.error('Error starting scan:', error);
            alert('Error starting scan: ' + error.message);
        }
    };

    window.downloadReport = (scanId, format) => {
        window.location.href = `/api/reports/${scanId}/download?format=${format}`;
    };

    window.deleteScan = async (scanId) => {
        if (!confirm('Are you sure you want to delete this scan report? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/scans/${scanId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                alert('Scan deleted successfully!');
                fetchScans(); // Refresh the scan list
            } else {
                const error = await response.json();
                alert('Failed to delete scan: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error deleting scan:', error);
            alert('Error deleting scan: ' + error.message);
        }
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

        // Top Hosts Chart
        const topHostsCtx = document.getElementById('topHostsChart');
        if (topHostsCtx) {
            // Destroy existing chart if any (to prevent canvas reuse issues)
            const existingChart = Chart.getChart(topHostsCtx);
            if (existingChart) existingChart.destroy();

            const labels = data.top_vulnerable_hosts.map(h => h.name);
            const counts = data.top_vulnerable_hosts.map(h => h.count);

            new Chart(topHostsCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Vulnerabilities',
                        data: counts,
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: '#EF4444',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            grid: { color: '#2D3748' },
                            ticks: { color: '#9CA3AF' },
                            beginAtZero: true
                        },
                        y: {
                            grid: { display: false },
                            ticks: { color: '#9CA3AF' }
                        }
                    }
                }
            });
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

    // ========== OpenVAS Configuration ==========
    async function loadOpenVASConfigs() {
        try {
            const response = await fetch('/api/openvas/configs');
            if (response.ok) {
                openvasConfigs = await response.json();
                const select = document.getElementById('openvasConfigSelect');
                const scheduleSelect = document.getElementById('scheduleOpenvasConfigSelect');

                if (select) {
                    select.innerHTML = '<option value="">Choose a configuration...</option>';
                    openvasConfigs.forEach(config => {
                        const option = document.createElement('option');
                        option.value = config.id;
                        option.textContent = config.name;
                        select.appendChild(option);
                    });
                }

                if (scheduleSelect) {
                    scheduleSelect.innerHTML = '<option value="">Choose a configuration...</option>';
                    openvasConfigs.forEach(config => {
                        const option = document.createElement('option');
                        option.value = config.id;
                        option.textContent = config.name;
                        scheduleSelect.appendChild(option);
                    });
                }
            } else {
                // OpenVAS not configured - this is OK, just disable the option
                console.log('OpenVAS not configured - only Nmap scanning available');
                const openvasOption = document.querySelector('input[value="openvas"]');
                if (openvasOption) {
                    openvasOption.disabled = true;
                    const label = openvasOption.closest('label');
                    if (label) {
                        label.style.opacity = '0.5';
                        label.title = 'OpenVAS not configured. See OPENVAS_SETUP.md for installation instructions.';
                    }
                }
            }
        } catch (error) {
            console.log('OpenVAS not available:', error.message);
            // Silently disable OpenVAS option - this is expected if OpenVAS isn't installed
        }
    }

    window.toggleOpenVASConfig = () => {
        const scanType = document.querySelector('input[name="scan_type"]:checked').value;
        const configGroup = document.getElementById('openvasConfigGroup');
        if (scanType === 'openvas') {
            configGroup.style.display = 'block';
            if (openvasConfigs.length === 0) {
                loadOpenVASConfigs();
            }
        } else {
            configGroup.style.display = 'none';
        }
    };

    window.toggleScheduleOpenVASConfig = () => {
        const scanType = document.querySelector('#newScheduleForm input[name="scan_type"]:checked').value;
        const nmapGroup = document.getElementById('scheduleNmapArgsGroup');
        const openvasGroup = document.getElementById('scheduleOpenvasConfigGroup');

        if (scanType === 'openvas') {
            nmapGroup.style.display = 'none';
            openvasGroup.style.display = 'block';
            if (openvasConfigs.length === 0) {
                loadOpenVASConfigs();
            }
        } else {
            nmapGroup.style.display = 'block';
            openvasGroup.style.display = 'none';
        }
    };

    // ========== Schedules Management ==========
    window.showNewScheduleModal = () => {
        document.getElementById('newScheduleModal').classList.remove('hidden');
        populateScheduleTargets();
        if (openvasConfigs.length === 0) {
            loadOpenVASConfigs();
        }
    };

    window.hideNewScheduleModal = () => {
        document.getElementById('newScheduleModal').classList.add('hidden');
    };

    function populateScheduleTargets() {
        fetch('/api/targets/')
            .then(res => res.json())
            .then(targets => {
                const select = document.getElementById('scheduleTargetSelect');
                select.innerHTML = '<option value="">Choose a target...</option>';
                targets.forEach(target => {
                    const option = document.createElement('option');
                    option.value = target.id;
                    option.textContent = `${target.name} (${target.ip_address})`;
                    select.appendChild(option);
                });
            });
    }

    window.applyCronPreset = () => {
        const preset = document.getElementById('cronPresets').value;
        if (preset) {
            document.getElementById('cronExpression').value = preset;
            validateCronExpression();
        }
    };

    async function validateCronExpression() {
        const cronExpr = document.getElementById('cronExpression').value;
        const validationDiv = document.getElementById('cronValidation');

        if (!cronExpr) {
            validationDiv.innerHTML = '';
            return;
        }

        try {
            const response = await fetch('/api/schedules/validate-cron', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cron_expression: cronExpr })
            });
            const data = await response.json();

            if (data.valid) {
                validationDiv.innerHTML = `<span style="color: var(--success-green);">✓ Valid - Next run: ${data.next_run_human}</span>`;
            } else {
                validationDiv.innerHTML = `<span style="color: var(--error-red);">✗ Invalid cron expression</span>`;
            }
        } catch (error) {
            console.error('Error validating cron:', error);
        }
    }

    // Validate cron on input
    const cronInput = document.getElementById('cronExpression');
    if (cronInput) {
        cronInput.addEventListener('input', debounce(validateCronExpression, 500));
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // New Schedule Form
    const newScheduleForm = document.getElementById('newScheduleForm');
    if (newScheduleForm) {
        newScheduleForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);

            const data = {
                name: formData.get('name'),
                description: formData.get('description'),
                target_id: parseInt(formData.get('target_id')),
                scan_type: formData.get('scan_type'),
                cron_expression: formData.get('cron_expression'),
                enabled: true
            };

            if (data.scan_type === 'nmap') {
                data.scanner_args = formData.get('scanner_args');
            } else if (data.scan_type === 'openvas') {
                const configId = formData.get('openvas_config_id');
                if (configId) {
                    data.openvas_config_id = configId;
                }
            }

            try {
                const response = await fetch('/api/schedules/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    hideNewScheduleModal();
                    fetchSchedules();
                    alert('Schedule created successfully!');
                } else {
                    const error = await response.json();
                    alert(`Failed to create schedule: ${error.error || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error creating schedule:', error);
                alert('Failed to create schedule');
            }
        });
    }

    async function fetchSchedules() {
        try {
            const response = await fetch('/api/schedules/');
            const schedules = await response.json();
            renderSchedules(schedules);
        } catch (error) {
            console.error('Error fetching schedules:', error);
        }
    }

    function renderSchedules(schedules) {
        const scheduleList = document.getElementById('scheduleList');
        if (!scheduleList) return;

        if (schedules.length === 0) {
            scheduleList.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">No schedules yet</td></tr>';
            return;
        }

        scheduleList.innerHTML = schedules.map(schedule => `
            <tr>
                <td>${schedule.name}</td>
                <td>${schedule.target_name || 'Unknown'}</td>
                <td><span class="badge badge-info">${schedule.scan_type}</span></td>
                <td><code style="font-size: 0.875rem;">${schedule.cron_expression}</code></td>
                <td>${schedule.next_run ? new Date(schedule.next_run).toLocaleString() : '-'}</td>
                <td>
                    <span class="badge badge-${schedule.enabled ? 'success' : 'secondary'}">
                        ${schedule.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                </td>
                <td>
                    <button onclick="toggleSchedule(${schedule.id})" class="btn btn-secondary" style="padding: 0.5rem 1rem; margin-right: 0.5rem;">
                        <i class="fas fa-${schedule.enabled ? 'pause' : 'play'}"></i>
                    </button>
                    <button onclick="deleteSchedule(${schedule.id})" class="btn btn-danger" style="padding: 0.5rem 1rem;">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    window.toggleSchedule = async (scheduleId) => {
        try {
            const response = await fetch(`/api/schedules/${scheduleId}/toggle`, {
                method: 'POST'
            });

            if (response.ok) {
                fetchSchedules();
            } else {
                alert('Failed to toggle schedule');
            }
        } catch (error) {
            console.error('Error toggling schedule:', error);
        }
    };

    window.deleteSchedule = async (scheduleId) => {
        if (!confirm('Are you sure you want to delete this schedule?')) return;

        try {
            const response = await fetch(`/api/schedules/${scheduleId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchSchedules();
                alert('Schedule deleted successfully!');
            } else {
                alert('Failed to delete schedule');
            }
        } catch (error) {
            console.error('Error deleting schedule:', error);
        }
    };

    // ========== Enhanced WebSocket for Real-time Nmap ==========
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

            // Real-time Nmap events
            socket.on('nmap_host_discovered', (data) => {
                if (data.scan_id === currentScanId) {
                    hostsDiscoveredCount = data.total_hosts;
                    document.getElementById('hostsDiscovered').textContent = data.total_hosts;
                    addLogEntry(`Host discovered: ${data.host}`, 'INFO');
                }
            });

            socket.on('nmap_port_discovered', (data) => {
                if (data.scan_id === currentScanId) {
                    portsDiscoveredCount = data.total_open_ports;
                    document.getElementById('portsDiscovered').textContent = data.total_open_ports;
                    addLogEntry(`Port ${data.port.port}/${data.port.protocol} (${data.port.service}) discovered`, 'INFO');
                }
            });

            socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
            });
        }
    }

    // Update showLiveScan to reset counters
    const originalShowLiveScan = window.showLiveScan;
    window.showLiveScan = (scanId, targetName) => {
        hostsDiscoveredCount = 0;
        portsDiscoveredCount = 0;
        document.getElementById('hostsDiscovered').textContent = '0';
        document.getElementById('portsDiscovered').textContent = '0';
        if (originalShowLiveScan) {
            originalShowLiveScan(scanId, targetName);
        }
    };

    // Update section navigation to load schedules
    const originalShowSection = showSection;
    showSection = (sectionId, clickedNavItem = null) => {
        originalShowSection(sectionId, clickedNavItem);
        if (sectionId === 'schedules') {
            fetchSchedules();
        }
    };

    // ========== Reports Management ==========
    async function fetchReports() {
        try {
            const response = await fetch('/api/reports/');
            const reports = await response.json();
            renderReports(reports);
        } catch (error) {
            console.error('Error fetching reports:', error);
        }
    }

    function renderReports(reports) {
        const reportsList = document.getElementById('reportsList');
        if (!reportsList) return;

        if (reports.length === 0) {
            reportsList.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-secondary);">No reports yet</td></tr>';
            return;
        }

        reportsList.innerHTML = reports.map(report => `
            <tr>
                <td><span class="badge badge-info">#${report.id}</span></td>
                <td>${report.title}</td>
                <td><span class="badge badge-${report.type === 'scan' ? 'success' : 'warning'}">${report.type}</span></td>
                <td><span class="badge badge-cyan">${report.format.toUpperCase()}</span></td>
                <td>${new Date(report.created_at).toLocaleString()}</td>
                <td>${getReportStatusBadge(report.status)}</td>
                <td>
                    ${report.status === 'completed' ?
                `<button onclick="downloadReportById(${report.id})" class="btn btn-primary" style="padding: 0.5rem 1rem;">
                            <i class="fas fa-download"></i> Download
                        </button>` :
                '<span style="color: var(--text-muted);">-</span>'}
                </td>
            </tr>
        `).join('');
    }

    function getReportStatusBadge(status) {
        const badges = {
            'completed': '<span class="badge badge-success">Completed</span>',
            'pending': '<span class="badge badge-warning">Pending</span>',
            'failed': '<span class="badge badge-error">Failed</span>'
        };
        return badges[status] || `<span class="badge">${status}</span>`;
    }

    window.showCreateReportModal = () => {
        document.getElementById('createReportModal').classList.remove('hidden');
        populateReportScans();
    };

    window.closeCreateReportModal = () => {
        document.getElementById('createReportModal').classList.add('hidden');
    };

    async function populateReportScans() {
        try {
            const response = await fetch('/api/scans/');
            const scans = await response.json();
            const select = document.getElementById('reportScanSelect');

            // Filter only completed scans
            const completedScans = scans.filter(s => s.status === 'completed');

            if (completedScans.length === 0) {
                select.innerHTML = '<option value="">No completed scans available</option>';
                return;
            }

            select.innerHTML = '<option value="">Choose a scan...</option>';
            completedScans.forEach(scan => {
                const option = document.createElement('option');
                option.value = scan.id;
                option.textContent = `#${scan.id} - ${scan.target_name} (${new Date(scan.created_at).toLocaleDateString()})`;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching scans:', error);
        }
    }

    window.generateReport = async (event) => {
        event.preventDefault();

        const scanId = document.getElementById('reportScanSelect').value;
        const format = document.getElementById('reportFormat').value;
        const type = document.getElementById('reportType').value;

        if (!scanId) {
            alert('Please select a scan');
            return;
        }

        try {
            const response = await fetch('/api/reports/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scan_id: parseInt(scanId),
                    format: format,
                    type: type
                })
            });

            if (response.ok) {
                closeCreateReportModal();
                fetchReports();
                alert('Report generated successfully!');
            } else {
                const error = await response.json();
                alert('Failed to generate report: ' + (error.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error generating report:', error);
            alert('Error generating report: ' + error.message);
        }
    };

    window.downloadReportById = (reportId) => {
        window.location.href = `/api/reports/${reportId}/download`;
    };

    // Initial data fetch
    fetchTargets();
    fetchScans();
    fetchStats();
    fetchTickets();

    // Auto-refresh scans every 10 seconds
    setInterval(fetchScans, 10000);
});

// Mobile Menu Functions (outside DOMContentLoaded to be globally accessible)
function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    sidebar.classList.toggle('mobile-open');
    overlay.classList.toggle('active');
}

function closeMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('active');
}

// Close mobile menu when clicking on nav items
document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeMobileMenu();
            }
        });
    });
});
