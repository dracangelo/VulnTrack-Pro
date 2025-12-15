document.addEventListener('DOMContentLoaded', () => {
    // Variable declarations
    let queueRefreshInterval = null;
    let progressPollInterval = null;
    let currentScanId = null;
    let socket = null;
    let hostsDiscoveredCount = 0;
    let portsDiscoveredCount = 0;
    let openvasConfigs = [];

    // ========== Authentication Logic ==========

    // Real-time validation for IP address
    const ipInput = document.querySelector('input[name="ip_address"]');
    if (ipInput) {
        ipInput.addEventListener('input', (e) => {
            const value = e.target.value;
            const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
            if (value && !ipRegex.test(value)) {
                e.target.setCustomValidity('Invalid IP address format');
                e.target.classList.add('input-error');
            } else {
                e.target.setCustomValidity('');
                e.target.classList.remove('input-error');
            }
        });
    }

    // 1. Check for token in URL (OAuth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');
    const errorFromUrl = urlParams.get('error');
    const inviteToken = urlParams.get('invite_token');

    if (tokenFromUrl) {
        localStorage.setItem('jwt_token', tokenFromUrl);
        window.history.replaceState({}, document.title, "/");
    }

    if (errorFromUrl) {
        UI.alert('Login Failed', `${urlParams.get('message') || 'Unknown error'}`, 'error');
        window.history.replaceState({}, document.title, "/");
    }

    if (inviteToken) {
        handleInviteToken(inviteToken);
    }

    // 2. Override fetch to add Authorization header
    const originalFetch = window.fetch;
    window.fetch = async function (url, options = {}) {
        const token = localStorage.getItem('jwt_token');

        // Skip adding header for auth endpoints to avoid loops if they don't need it (though most do)
        // But mainly we need it for API calls.

        if (token && url.startsWith('/api/')) {
            options.headers = options.headers || {};
            // If headers is not an instance of Headers, treat as object
            if (!(options.headers instanceof Headers)) {
                options.headers['Authorization'] = `Bearer ${token}`;
            } else {
                options.headers.append('Authorization', `Bearer ${token}`);
            }
        }

        try {
            const response = await originalFetch(url, options);

            // Handle 401 Unauthorized
            if (response.status === 401) {
                console.warn('Unauthorized access. Redirecting to login.');
                localStorage.removeItem('jwt_token');
                showLoginModal();
            }

            return response;
        } catch (error) {
            throw error;
        }
    };

    // 3. Check Authentication State
    function checkAuth() {
        const token = localStorage.getItem('jwt_token');
        if (!token) {
            showLoginModal();
        } else {
            // Optional: Verify token validity with /api/auth/me
            // For now, we assume it's valid until 401
            document.getElementById('loginModal').classList.add('hidden');
        }
    }

    // 4. Login Modal Logic
    async function showLoginModal() {
        const modal = document.getElementById('loginModal');
        modal.classList.remove('hidden');

        const providersContainer = document.getElementById('loginProviders');
        const loading = document.getElementById('loginLoading');

        try {
            // Use originalFetch to avoid 401 loop if this endpoint was protected (it shouldn't be)
            // But actually, get_providers is likely public. Let's check auth_routes.py.
            // It is NOT decorated with @jwt_required. Good.
            const response = await originalFetch('/api/auth/providers');
            const data = await response.json();

            loading.style.display = 'none';
            providersContainer.innerHTML = '';

            if (data.providers && data.providers.length > 0) {
                data.providers.forEach(provider => {
                    const btn = document.createElement('button');
                    btn.className = 'btn btn-secondary'; // Changed to secondary to distinguish from main action
                    btn.style.width = '100%';
                    btn.style.marginBottom = '0.5rem';
                    btn.innerHTML = `<i class="fab fa-${provider.name}"></i> Sign in with ${provider.display_name}`;
                    btn.onclick = () => {
                        window.location.href = `/api/auth/login/${provider.name}`;
                    };
                    providersContainer.appendChild(btn);
                });
            } else {
                // If no providers, hide the container or show message
                // providersContainer.innerHTML = '<p>No OAuth providers configured.</p>';
            }

        } catch (error) {
            console.error('Error fetching providers:', error);
            loading.textContent = 'Failed to load login providers.';
        }
    }

    // 5. Auth Form Handlers
    window.handleLogin = async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const errorDiv = document.getElementById('loginError');

        try {
            const response = await originalFetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('jwt_token', data.token);
                localStorage.setItem('user_info', JSON.stringify(data.user)); // Store user info
                document.getElementById('loginModal').classList.add('hidden');
                window.location.reload(); // Reload to refresh state
            } else {
                errorDiv.textContent = data.error || 'Login failed';
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = 'Network error occurred';
            errorDiv.style.display = 'block';
        }
    };

    window.handleRegister = async (e) => {
        e.preventDefault();
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        const errorDiv = document.getElementById('loginError');

        try {
            const response = await originalFetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('jwt_token', data.token);
                localStorage.setItem('user_info', JSON.stringify(data.user));
                document.getElementById('loginModal').classList.add('hidden');
                window.location.reload();
            } else {
                errorDiv.textContent = data.error || 'Registration failed';
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = 'Network error occurred';
            errorDiv.style.display = 'block';
        }
    };

    window.toggleAuthMode = (e) => {
        e.preventDefault();
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const title = document.getElementById('authModalTitle');
        const subtitle = document.getElementById('authModalSubtitle');
        const link = document.getElementById('authToggleLink');
        const errorDiv = document.getElementById('loginError');

        errorDiv.style.display = 'none';

        if (loginForm.classList.contains('hidden')) {
            // Switch to Login
            loginForm.classList.remove('hidden');
            registerForm.classList.add('hidden');
            title.textContent = 'Welcome to VulnTrack';
            subtitle.textContent = 'Please sign in to continue';
            link.textContent = 'Need an account? Register';
        } else {
            // Switch to Register
            loginForm.classList.add('hidden');
            registerForm.classList.remove('hidden');
            title.textContent = 'Create Account';
            subtitle.textContent = 'Join VulnTrack today';
            link.textContent = 'Already have an account? Sign In';
        }
        // Check for invites
        if (window.checkInvite) {
            window.checkInvite();
        }
    };

    // Initial Auth Check
    checkAuth();

    // Navigation handling

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
            fetchStats();
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
        } else if (sectionId === 'teams') {
            fetchTeams();
        } else if (sectionId === 'users') {
            fetchUsers();
        } else if (sectionId === 'profile') {
            fetchProfile();
        } else if (sectionId === 'notifications') {
            if (typeof fetchNotifications === 'function') {
                fetchNotifications();
            }
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
    window.switchTargetTab = function (tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');

        // Show/hide forms
        document.querySelectorAll('.target-form').forEach(form => {
            form.classList.add('hidden');
        });
        document.querySelector(`.target-form[data-form="${tabName}"]`).classList.remove('hidden');
    };

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
            if (scanType === 'nmap_full') {
                requestData.args = '-sS -sV -sC -p1-65535 -Pn -O -A --script vuln';
            } else {
                // Nmap Quick with vulnerability scanning
                requestData.args = '-F -sV --script vuln';
            }
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
                UI.toast('Scan started successfully', 'success');
            } else {
                UI.toast('Failed to start scan', 'error');
            }
        } catch (error) {
            console.error('Error starting scan:', error);
            UI.toast('Error starting scan', 'error');
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
                <td>
                    <input type="checkbox" class="target-checkbox" value="${target.id}" 
                           onchange="updateBulkDeleteButton()" 
                           style="cursor: pointer; width: 18px; height: 18px;">
                </td>
                <td>${target.name || 'Unnamed'}</td>
                <td><span class="badge badge-cyan">${target.ip_address}</span></td>
                <td>${target.description || '-'}</td>
                <td>
                    <button onclick="startScan(${target.id})" class="btn btn-primary" style="padding: 0.5rem 1rem; margin-right: 0.5rem;">
                        <i class="fas fa-radar"></i> Scan
                    </button>
                    <button onclick="deleteTarget(${target.id})" class="btn btn-danger" style="padding: 0.5rem 1rem;">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </td>
            </tr>
        `).join('');

        // Reset select all checkbox
        const selectAll = document.getElementById('selectAllTargets');
        if (selectAll) selectAll.checked = false;
        updateBulkDeleteButton();
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

            socket.on('scan_log', (data) => {
                if (data.scan_id === currentScanId) {
                    addLogEntry(data.message, 'RAW');
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
        if (data.elapsed_seconds !== undefined && data.elapsed_seconds !== null) {
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

        if (level === 'RAW') {
            logLine.style.fontFamily = 'monospace';
            logLine.style.whiteSpace = 'pre-wrap';
            logLine.style.color = '#a0aec0';
            logLine.style.fontSize = '0.85rem';
            logLine.innerHTML = `<span>${message}</span>`;
        } else {
            logLine.innerHTML = `
                <span class="log-timestamp">[${timestamp}]</span>
                <span class="log-level-${level}">[${level}]</span>
                <span>${message}</span>
            `;
        }

        logContainer.appendChild(logLine);
        logContainer.scrollTop = logContainer.scrollHeight;

        // Keep only last 50 entries
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    window.cancelScan = async () => {
        if (!await UI.confirm('Are you sure you want to cancel this scan?')) return;

        try {
            const response = await fetch(`/api/scans/${currentScanId}/cancel`, {
                method: 'DELETE'
            });

            if (response.ok) {
                addLogEntry('Scan cancellation requested', 'WARN');
                stopProgressPolling();
                UI.toast('Scan cancellation requested', 'info');
                setTimeout(() => {
                    closeLiveScan();
                }, 1000);
            } else {
                const error = await response.json();
                UI.toast(`Failed to cancel scan: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Error cancelling scan:', error);
            UI.toast('Failed to cancel scan', 'error');
        }
    };

    // Add new target (Single IP)
    const addTargetForm = document.getElementById('addTargetForm');
    if (addTargetForm) {
        addTargetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                input: formData.get('ip_address'),
                type: 'ip',
                name: formData.get('name') || formData.get('ip_address'),
                description: formData.get('description')
            };

            try {
                const response = await fetch('/api/targets/bulk', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                if (response.ok) {
                    e.target.reset();
                    fetchTargets();
                    UI.toast('Target added successfully!', 'success');
                } else {
                    const error = await response.json();
                    UI.toast(`Failed to add target: ${error.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                console.error('Error adding target:', error);
                UI.toast('Error adding target: ' + error.message, 'error');
            }
        });
    }

    // Add Range/CIDR Form
    const addRangeForm = document.getElementById('addRangeForm');
    if (addRangeForm) {
        addRangeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const cidr = formData.get('cidr');
            const description = formData.get('description');
            const keepAsSingle = document.getElementById('keepAsSingle').checked;

            // Show loading indicator
            const submitBtn = e.target.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding targets...';
            submitBtn.disabled = true;

            try {
                const response = await fetch('/api/targets/bulk', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        input: cidr,
                        type: 'cidr',
                        description: description,
                        keep_as_single: keepAsSingle
                    })
                });

                const result = await response.json();

                if (response.ok) {
                    e.target.reset();
                    fetchTargets();

                    let message;
                    if (keepAsSingle) {
                        message = `CIDR target created successfully!\nCIDR: ${result.cidr}`;
                    } else {
                        message = `Successfully added ${result.created} targets from CIDR range!`;
                        if (result.errors && result.errors.length > 0) {
                            message += `\n\nSkipped (already exist): ${result.errors.join(', ')}`;
                        }
                    }
                    UI.alert('Targets Added', message, 'success');
                } else {
                    UI.toast(`Failed to add targets: ${result.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                console.error('Error adding targets from CIDR:', error);
                UI.toast('Error adding targets: ' + error.message, 'error');
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // Add target from hostname
    const addHostnameForm = document.getElementById('addHostnameForm');
    if (addHostnameForm) {
        addHostnameForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const hostname = formData.get('hostname');
            const description = formData.get('description');

            // Show loading indicator
            const submitBtn = e.target.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resolving hostname...';
            submitBtn.disabled = true;

            try {
                const response = await fetch('/api/targets/bulk', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        input: hostname,
                        type: 'hostname',
                        description: description
                    })
                });

                const result = await response.json();

                if (response.ok) {
                    e.target.reset();
                    fetchTargets();
                    UI.alert('Target Added', `Hostname: ${result.hostname}\nResolved IP: ${result.ip_address}`, 'success');
                } else {
                    UI.toast(`Failed to add target: ${result.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                console.error('Error adding target from hostname:', error);
                UI.toast('Error adding target: ' + error.message, 'error');
            } finally {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // Delete target
    window.deleteTarget = async (id) => {
        if (!await UI.confirm('Are you sure you want to delete this target?')) return;

        try {
            const response = await fetch(`/api/targets/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchTargets();
                UI.toast('Target deleted successfully!', 'success');
            } else {
                UI.toast('Failed to delete target', 'error');
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
                : ''}
                    
                    ${scan.status === 'running' ?
                `<button onclick="stopScan(${scan.id})" class="btn btn-warning" style="padding: 0.5rem 1rem; margin-right: 0.5rem;">
                            <i class="fas fa-stop"></i> Stop
                        </button>`
                : ''}

                    ${scan.status !== 'running' ?
                `<button onclick="deleteScan(${scan.id})" class="btn btn-danger" style="padding: 0.5rem 1rem;">
                            <i class="fas fa-trash"></i> Delete
                        </button>`
                : ''}
                </td>
            </tr>
        `).join('');
    }

    window.stopScan = async (id) => {
        if (!await UI.confirm('Are you sure you want to stop this scan?')) return;

        try {
            const response = await fetch(`/api/scans/${id}/cancel`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchScans();
                UI.toast('Scan stop requested', 'info');
            } else {
                const error = await response.json();
                UI.toast(`Failed to stop scan: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('Error stopping scan:', error);
            UI.toast('Failed to stop scan', 'error');
        }
    };

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
                fetchScans();
                refreshQueueStatus();
                UI.toast('Scan started successfully', 'success');
            } else {
                UI.toast('Failed to start scan', 'error');
            }
        } catch (error) {
            console.error('Error starting scan:', error);
            UI.toast('Error starting scan: ' + error.message, 'error');
        }
    };

    window.downloadReport = (scanId, format) => {
        if (format === 'pdf') {
            window.location.href = `/api/reports/scan/${scanId}/pdf`;
        } else {
            // For HTML, we might need to generate it first or use a different route
            // For now, let's assume the existing route was intended for reports, not scans.
            // But since we don't have a direct HTML download for scan ID yet (except via view), 
            // let's leave it or alert.
            // Actually, let's just use the view route for HTML
            window.open(`/api/scans/${scanId}/report`, '_blank');
        }
    };

    window.deleteScan = async (id) => {
        if (!await UI.confirm('Are you sure you want to delete this scan report? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/scans/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchScans();
                UI.toast('Scan deleted successfully!', 'success');
            } else {
                const error = await response.json();
                UI.toast('Failed to delete scan: ' + (error.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error deleting scan:', error);
            UI.toast('Error deleting scan: ' + error.message, 'error');
        }
    };

    // Dashboard - Fetch stats
    async function fetchStats(targetId = null) {
        try {
            let url = '/api/reports/stats';
            if (targetId) {
                url += `?target_id=${targetId}`;
            }
            const response = await fetch(url);
            const data = await response.json();
            renderDashboard(data, targetId);

            // Also fetch activity feed
            fetchActivityFeed();
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }

    async function fetchActivityFeed() {
        try {
            const response = await fetch('/api/collaboration/activity');
            const activities = await response.json();
            renderActivityFeed(activities);
        } catch (error) {
            console.error('Error fetching activity feed:', error);
        }
    }

    function renderActivityFeed(activities) {
        const activityList = document.getElementById('recentActivity');
        if (!activityList) return;

        if (activities.length === 0) {
            activityList.innerHTML = '<tr><td colspan="4" class="text-center">No recent activity</td></tr>';
            return;
        }

        activityList.innerHTML = activities.map(activity => `
            <tr>
                <td>${new Date(activity.timestamp).toLocaleString()}</td>
                <td>
                    <strong>${activity.user}</strong> ${activity.action.replace('_', ' ')}
                </td>
                <td>${activity.target_type} #${activity.target_id}</td>
                <td>${activity.details}</td>
            </tr>
        `).join('');
    }

    window.clearHostSelection = function () {
        fetchStats(null);
    };

    let severityChartInstance = null;
    let topHostsChartInstance = null;

    function renderDashboard(data, targetId = null) {
        // Severity Chart
        const ctx = document.getElementById('severityChart');
        if (ctx) {
            if (severityChartInstance) {
                severityChartInstance.destroy();
            }

            const severityOrder = ['Critical', 'High', 'Medium', 'Low', 'Info'];
            const counts = severityOrder.map(sev => data.severity_counts[sev] || 0);
            const totalVulns = counts.reduce((a, b) => a + b, 0);

            // Update card title to reflect filter
            const severityCardTitle = ctx.closest('.card').querySelector('.card-title');
            if (severityCardTitle) {
                if (targetId && data.selected_host) {
                    severityCardTitle.textContent = `Vulnerabilities: ${data.selected_host.name}`;

                    // Add a reset button if not exists
                    if (!severityCardTitle.querySelector('.reset-btn')) {
                        const resetBtn = document.createElement('button');
                        resetBtn.className = 'btn btn-xs btn-secondary reset-btn';
                        resetBtn.style.marginLeft = '10px';
                        resetBtn.innerHTML = '<i class="fas fa-undo"></i> Reset';
                        resetBtn.onclick = (e) => {
                            e.stopPropagation();
                            fetchStats(null);
                        };
                        severityCardTitle.appendChild(resetBtn);
                    }
                } else {
                    severityCardTitle.textContent = 'Vulnerabilities by Severity';
                    // Remove reset button if it exists
                    const existingResetBtn = severityCardTitle.querySelector('.reset-btn');
                    if (existingResetBtn) {
                        existingResetBtn.remove();
                    }
                }
            }

            severityChartInstance = new Chart(ctx.getContext('2d'), {
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
                        },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }

        // Top Hosts Chart
        const topHostsCtx = document.getElementById('topHostsChart');
        if (topHostsCtx) {
            // Destroy existing chart if it exists to allow re-rendering with updated selection
            if (topHostsChartInstance) {
                topHostsChartInstance.destroy();
                topHostsChartInstance = null;
            }

            const labels = data.top_vulnerable_hosts.map(h => h.name);
            const counts = data.top_vulnerable_hosts.map(h => h.count);
            const ids = data.top_vulnerable_hosts.map(h => h.id);

            // Highlight selected host with different color
            const backgroundColors = ids.map(id =>
                (targetId && id === targetId) ? 'rgba(16, 185, 129, 0.8)' : 'rgba(239, 68, 68, 0.8)'
            );
            const borderColors = ids.map(id =>
                (targetId && id === targetId) ? '#10B981' : '#EF4444'
            );

            topHostsChartInstance = new Chart(topHostsCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Vulnerabilities',
                        data: counts,
                        backgroundColor: backgroundColors,
                        borderColor: borderColors,
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                footer: () => 'Click to view vulnerabilities for this host'
                            }
                        }
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
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const clickedTargetId = ids[index];
                            // Toggle selection: if clicking the same host, deselect it
                            if (targetId === clickedTargetId) {
                                fetchStats(null);
                            } else {
                                fetchStats(clickedTargetId);
                            }
                        } else {
                            // Clicked background - reset
                            fetchStats(null);
                        }
                    },
                    onHover: (event, elements) => {
                        event.native.target.style.cursor = elements.length ? 'pointer' : 'default';
                    }
                }
            });
        }

        // Display selected host information
        const selectedHostCard = document.getElementById('selectedHostCard');
        const selectedHostContent = document.getElementById('selectedHostContent');
        if (selectedHostCard && selectedHostContent) {
            if (targetId && data.selected_host) {
                const host = data.selected_host;
                const severityOrder = ['Critical', 'High', 'Medium', 'Low', 'Info'];
                const severityColors = {
                    'Critical': '#EF4444',
                    'High': '#F59E0B',
                    'Medium': '#EAB308',
                    'Low': '#10B981',
                    'Info': '#3B82F6'
                };

                let severityBreakdown = '';
                severityOrder.forEach(sev => {
                    const count = data.severity_counts[sev] || 0;
                    if (count > 0) {
                        severityBreakdown += `
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                <div style="width: 12px; height: 12px; background-color: ${severityColors[sev]}; border-radius: 2px;"></div>
                                <span style="color: var(--text-secondary);">${sev}:</span>
                                <span style="font-weight: 600; color: var(--text-primary);">${count}</span>
                            </div>
                        `;
                    }
                });

                selectedHostContent.innerHTML = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem;">
                        <div>
                            <h4 style="font-size: 1.125rem; font-weight: 600; color: var(--text-primary); margin-bottom: 1rem;">
                                ${host.name}
                            </h4>
                            <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                                <div>
                                    <span style="font-size: 0.875rem; color: var(--text-secondary);">IP Address:</span>
                                    <div style="font-weight: 500; color: var(--text-primary);">${host.ip_address || 'N/A'}</div>
                                </div>
                                <div>
                                    <span style="font-size: 0.875rem; color: var(--text-secondary);">Total Vulnerabilities:</span>
                                    <div style="font-size: 1.5rem; font-weight: 700; color: var(--accent-cyan);">${host.count}</div>
                                </div>
                            </div>
                        </div>
                        <div>
                            <h4 style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.75rem;">Severity Breakdown</h4>
                            ${severityBreakdown || '<div style="color: var(--text-secondary);">No vulnerabilities found</div>'}
                        </div>
                    </div>
                `;
                selectedHostCard.classList.remove('hidden');
            } else {
                selectedHostCard.classList.add('hidden');
                selectedHostContent.innerHTML = '';
            }
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
                    UI.toast('Schedule created successfully!', 'success');
                } else {
                    const error = await response.json();
                    UI.toast(`Failed to create schedule: ${error.error || 'Unknown error'}`, 'error');
                }
            } catch (error) {
                console.error('Error creating schedule:', error);
                UI.toast('Failed to create schedule', 'error');
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
                UI.toast('Schedule updated successfully', 'success');
            } else {
                UI.toast('Failed to toggle schedule', 'error');
            }
        } catch (error) {
            console.error('Error toggling schedule:', error);
        }
    };

    window.deleteSchedule = async (id) => {
        if (!await UI.confirm('Are you sure you want to delete this schedule?')) return;

        try {
            const response = await fetch(`/api/schedules/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchSchedules();
                UI.toast('Schedule deleted successfully!', 'success');
            } else {
                UI.toast('Failed to delete schedule', 'error');
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
            UI.toast('Please select a scan', 'warning');
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
                fetchReports();
                closeCreateReportModal(); // Changed from hideCreateReportModal to closeCreateReportModal
                UI.toast('Report generated successfully!', 'success');
            } else {
                const error = await response.json();
                UI.toast('Failed to generate report: ' + (error.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error generating report:', error);
            UI.toast('Error generating report: ' + error.message, 'error');
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

    // ========== Bulk Delete Functions ==========
    window.toggleSelectAll = () => {
        const selectAll = document.getElementById('selectAllTargets');
        const checkboxes = document.querySelectorAll('.target-checkbox');
        checkboxes.forEach(cb => cb.checked = selectAll.checked);
        updateBulkDeleteButton();
    };

    window.updateBulkDeleteButton = () => {
        const checkboxes = document.querySelectorAll('.target-checkbox:checked');
        const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
        const selectedCount = document.getElementById('selectedCount');

        if (checkboxes.length > 0) {
            bulkDeleteBtn.style.display = 'inline-block';
            selectedCount.textContent = checkboxes.length;
        } else {
            bulkDeleteBtn.style.display = 'none';
        }
    };

    window.bulkDeleteTargets = async () => {
        const selectedCheckboxes = document.querySelectorAll('.target-checkbox:checked');
        const targetIds = Array.from(selectedCheckboxes).map(cb => parseInt(cb.value));

        if (targetIds.length === 0) {
            UI.toast('Please select at least one target to delete', 'warning');
            return;
        }

        if (!await UI.confirm(`Are you sure you want to delete ${targetIds.length} target(s)? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch('/api/targets/bulk-delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_ids: targetIds })
            });

            const result = await response.json();

            if (response.ok) {
                fetchTargets();
                UI.toast(`Successfully deleted ${result.deleted_count} target(s)`, 'success');
            } else {
                UI.toast('Failed to delete targets: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Error deleting targets:', error);
            UI.toast('Error deleting targets: ' + error.message, 'error');
        }
    };

    window.deleteTarget = async (id) => {
        if (!await UI.confirm('Are you sure you want to delete this target?')) return;

        try {
            const response = await fetch(`/api/targets/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                fetchTargets();
                UI.toast('Target deleted successfully', 'success');
            } else {
                UI.toast('Failed to delete target', 'error');
            }
        } catch (error) {
            console.error('Error deleting target:', error);
            UI.toast('Error deleting target: ' + error.message, 'error');
        }
    };
});

// Mobile Menu Functions (outside DOMContentLoaded to be globally accessible)
function toggleMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    sidebar.classList.toggle('mobile-open');
    overlay.classList.toggle('active');

    // Toggle hamburger animation
    const hamburger = document.querySelector('.hamburger');
    if (hamburger) {
        hamburger.classList.toggle('active');
    }
}

function closeMobileMenu() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.mobile-overlay');
    const hamburger = document.querySelector('.hamburger');

    sidebar.classList.remove('mobile-open');
    overlay.classList.remove('active');

    if (hamburger) {
        hamburger.classList.remove('active');
    }
}

// Initialize mobile menu on page load
function initMobileMenu() {
    const menuToggle = document.getElementById('mobileMenuToggle');
    const overlay = document.getElementById('mobileOverlay');
    const navItems = document.querySelectorAll('.nav-item');

    if (menuToggle) {
        menuToggle.addEventListener('click', toggleMobileMenu);
    }

    if (overlay) {
        overlay.addEventListener('click', closeMobileMenu);
    }

    // Close menu when nav item clicked on mobile
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeMobileMenu();
            }
            // Invite Handling
            async function handleInviteToken(token) {
                try {
                    const response = await fetch(`/api/auth/invite/${token}`);
                    const data = await response.json();

                    if (response.ok && data.valid) {
                        // Show registration modal
                        const modal = document.getElementById('loginModal');
                        modal.classList.add('hidden'); // Hide login if open

                        // We need a registration modal. For now, let's reuse/adapt the login modal or create a new one dynamically
                        // Or better, assume there's a register modal or form we can show.
                        // Let's create a simple dynamic modal for registration

                        const registerHtml = `
                    <div id="registerModal" class="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50">
                        <div class="bg-gray-800 p-8 rounded-lg shadow-xl border border-cyan-500/30 w-full max-w-md relative">
                            <h2 class="text-2xl font-bold mb-6 text-cyan-400 font-display">Complete Registration</h2>
                            <p class="mb-4 text-gray-300">You have been invited as <strong class="text-white">${data.role}</strong>.</p>
                            
                            <form id="registerForm" onsubmit="registerWithInvite(event, '${token}')">
                                <div class="mb-4">
                                    <label class="block text-gray-400 mb-2">Email</label>
                                    <input type="email" value="${data.email}" disabled class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-gray-500 cursor-not-allowed">
                                </div>
                                <div class="mb-4">
                                    <label class="block text-gray-400 mb-2">Username</label>
                                    <input type="text" id="regUsername" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:border-cyan-500 focus:outline-none">
                                </div>
                                <div class="mb-6">
                                    <label class="block text-gray-400 mb-2">Password</label>
                                    <input type="password" id="regPassword" required class="w-full bg-gray-900 border border-gray-700 rounded p-2 text-white focus:border-cyan-500 focus:outline-none">
                                </div>
                                <button type="submit" class="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-bold py-2 px-4 rounded transition-colors">
                                    Register
                                </button>
                            </form>
                        </div>
                    </div>
                `;

                        document.body.insertAdjacentHTML('beforeend', registerHtml);

                    } else {
                        UI.alert('Invalid Invite', data.error || 'This invite link is invalid or expired.', 'error');
                        window.history.replaceState({}, document.title, "/");
                    }
                } catch (error) {
                    console.error('Error validating invite:', error);
                    UI.alert('Error', 'Failed to validate invite link.', 'error');
                }
            }

            window.registerWithInvite = async (event, token) => {
                event.preventDefault();

                const username = document.getElementById('regUsername').value;
                const password = document.getElementById('regPassword').value;

                await UI.asyncOperation(async () => {
                    const response = await fetch('/api/auth/register/invite', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token, username, password })
                    });

                    const result = await response.json();

                    if (response.ok) {
                        localStorage.setItem('jwt_token', result.token);
                        document.getElementById('registerModal').remove();
                        window.history.replaceState({}, document.title, "/");
                        UI.toast('Registration successful! Welcome.', 'success');
                        setTimeout(() => window.location.reload(), 1000);
                    } else {
                        throw new Error(result.error || 'Registration failed');
                    }
                }, 'Registering...');
            };

        });
    });

    // Close menu on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && window.innerWidth <= 768) {
            closeMobileMenu();
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initMobileMenu);
