// Notification Management

let unreadNotificationCount = 0;

document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch
    fetchNotifications();

    // Poll every minute
    setInterval(fetchNotifications, 60000);
});

async function fetchNotifications() {
    try {
        const response = await fetch('/api/notifications');
        if (response.status === 401) return; // Not logged in

        const notifications = await response.json();
        updateNotificationUI(notifications);
    } catch (error) {
        console.error('Error fetching notifications:', error);
    }
}

function updateNotificationUI(notifications) {
    const unread = notifications.filter(n => !n.is_read);
    unreadNotificationCount = unread.length;

    // Update Sidebar Badge
    const sidebarBadge = document.getElementById('notificationBadge');
    if (sidebarBadge) {
        if (unreadNotificationCount > 0) {
            sidebarBadge.textContent = unreadNotificationCount;
            sidebarBadge.style.display = 'inline-flex';
        } else {
            sidebarBadge.style.display = 'none';
        }
    }

    // Render list in the Notifications Section (if active)
    const list = document.getElementById('notificationsList');
    if (list) {
        renderNotificationsList(notifications, list);
    }
}

function renderNotificationsList(notifications, container) {
    if (notifications.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--text-secondary);">
                <i class="fas fa-bell-slash" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <p>No notifications yet</p>
            </div>
        `;
        return;
    }

    container.innerHTML = notifications.map(n => `
        <div class="notification-item ${n.is_read ? 'read' : 'unread'}" onclick="handleNotificationClick(${n.id}, '${n.link}', '${n.type}')">
            <div class="notification-icon">
                <i class="fas ${getNotificationIcon(n.type)}"></i>
            </div>
            <div class="notification-content">
                <div class="notification-message">${n.message}</div>
                <div class="notification-time">${new Date(n.created_at).toLocaleString()}</div>
            </div>
            ${!n.is_read ? '<div class="notification-dot"></div>' : ''}
        </div>
    `).join('');
}

function getNotificationIcon(type) {
    switch (type) {
        case 'mention': return 'fa-at';
        case 'assignment': return 'fa-user-tag';
        case 'system': return 'fa-cog';
        default: return 'fa-bell';
    }
}

async function handleNotificationClick(id, link, type) {
    // 1. Mark as read
    try {
        await fetch(`/api/notifications/${id}/read`, { method: 'PUT' });
        fetchNotifications(); // Refresh UI
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }

    // 2. Navigate/Action
    if (link) {
        if (link.startsWith('/vulnerabilities/')) {
            const vulnId = link.split('/').pop();
            // Switch to vulnerabilities section
            if (typeof window.showSection === 'function') {
                window.showSection('vulnerabilities');
            }

            // Wait a bit for section to load/init if needed, then show details
            openVulnerabilityFromNotification(vulnId);
        } else if (link.startsWith('/tickets/')) {
            if (typeof window.showSection === 'function') {
                window.showSection('tickets');
            }
            // Implement ticket detail view if exists
        }
    }
}

async function openVulnerabilityFromNotification(vulnId) {
    try {
        // Fetch the vulnerability instance directly
        const instanceRes = await fetch(`/api/vulns/instances/${vulnId}`);
        if (!instanceRes.ok) {
            console.error('Failed to fetch vulnerability instance');
            UI.toast('Failed to load vulnerability', 'error');
            return;
        }

        const vuln = await instanceRes.json();
        console.log('Fetched instance:', vuln);

        // Fetch the vulnerability definition for description and remediation
        const vulnDefResponse = await fetch(`/api/vulns/${vuln.vulnerability_id}`);
        if (!vulnDefResponse.ok) {
            console.error('Failed to fetch vulnerability definition');
            UI.toast('Failed to load vulnerability details', 'error');
            return;
        }

        const vulnDef = await vulnDefResponse.json();
        console.log('Fetched vulnerability definition:', vulnDef);

        // Switch to vulnerabilities section first
        if (typeof window.showSection === 'function') {
            window.showSection('vulnerabilities');
        }

        // Set the target context for consistency
        const targetSelect = document.getElementById('vulnTargetSelect');
        if (targetSelect) {
            targetSelect.value = vuln.target_id;
            window.currentVulnTargetId = vuln.target_id;
        }

        // Populate the modal directly with the fetched data
        document.getElementById('vulnDetailTitle').textContent = vuln.vulnerability_name || 'Unknown Vulnerability';
        document.getElementById('vulnDetailCVE').textContent = vulnDef.cve_id ? `CVE: ${vulnDef.cve_id}` : '';

        // Use the helper function if it exists
        if (typeof window.getSeverityBadge === 'function') {
            document.getElementById('vulnDetailSeverity').innerHTML = window.getSeverityBadge(vuln.severity);
        } else {
            document.getElementById('vulnDetailSeverity').textContent = vuln.severity;
        }

        document.getElementById('vulnDetailCVSS').textContent = vuln.cvss_score ? vuln.cvss_score.toFixed(1) : 'N/A';

        if (typeof window.getVulnStatusBadge === 'function') {
            document.getElementById('vulnDetailStatus').innerHTML = window.getVulnStatusBadge(vuln.status);
        } else {
            document.getElementById('vulnDetailStatus').textContent = vuln.status;
        }

        document.getElementById('vulnDetailDetected').textContent = vuln.detected_at ?
            new Date(vuln.detected_at).toLocaleString() : 'Unknown';
        document.getElementById('vulnDetailTarget').textContent = vuln.target_name || 'Unknown';

        const portInfo = [];
        if (vuln.port) portInfo.push(`Port ${vuln.port}`);
        if (vuln.protocol) portInfo.push(vuln.protocol.toUpperCase());
        if (vuln.service) portInfo.push(vuln.service);
        document.getElementById('vulnDetailPort').textContent = portInfo.length > 0 ? portInfo.join(' / ') : 'N/A';

        document.getElementById('vulnDetailDescription').textContent = vulnDef.description || 'No description available.';

        // Evidence
        if (vuln.evidence) {
            document.getElementById('vulnDetailEvidenceSection').style.display = 'block';
            document.getElementById('vulnDetailEvidence').textContent = vuln.evidence;
        } else {
            document.getElementById('vulnDetailEvidenceSection').style.display = 'none';
        }

        // Remediation
        if (vulnDef.remediation) {
            document.getElementById('vulnDetailRemediationSection').style.display = 'block';
            document.getElementById('vulnDetailRemediation').textContent = vulnDef.remediation;
        } else {
            document.getElementById('vulnDetailRemediationSection').style.display = 'none';
        }

        // Set instance ID and status for update form
        document.getElementById('vulnDetailInstanceId').value = vuln.id;
        document.getElementById('vulnNewStatus').value = vuln.status;

        // Show modal
        const modal = document.getElementById('vulnDetailsModal');
        if (modal) {
            modal.classList.remove('hidden');
        }

        // Switch to comments tab
        setTimeout(() => {
            if (typeof window.switchVulnTab === 'function') {
                window.switchVulnTab('comments');
            }
        }, 300);

        console.log('Vulnerability details loaded successfully from notification');

    } catch (e) {
        console.error('Error opening vuln:', e);
        UI.toast('Failed to open vulnerability', 'error');
    }
}

async function markAllNotificationsRead() {
    if (!await UI.confirm('Mark all notifications as read?')) return;

    try {
        await fetch('/api/notifications/read-all', { method: 'PUT' });
        fetchNotifications();
        UI.toast('All notifications marked as read', 'success');
    } catch (error) {
        console.error('Error:', error);
    }
}
