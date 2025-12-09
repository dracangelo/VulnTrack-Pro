// ========== Vulnerability Management ==========
let currentVulnTargetId = null;

// Populate target dropdown when vulnerabilities section is loaded
function populateVulnTargets() {
    fetch('/api/targets/')
        .then(res => res.json())
        .then(targets => {
            const select = document.getElementById('vulnTargetSelect');
            select.innerHTML = '<option value="">Choose a target to view vulnerabilities...</option>';
            targets.forEach(target => {
                const option = document.createElement('option');
                option.value = target.id;
                option.textContent = `${target.name} (${target.ip_address})`;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching targets:', error));
}

// Populate host filter dropdown
function populateVulnHosts() {
    fetch('/api/targets/')
        .then(res => res.json())
        .then(targets => {
            const select = document.getElementById('vulnHostFilter');
            select.innerHTML = '<option value="">All Hosts</option>';
            targets.forEach(target => {
                const option = document.createElement('option');
                option.value = target.id;
                option.textContent = `${target.name} (${target.ip_address})`;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching hosts:', error));
}

// Populate group filter dropdown
function populateVulnGroups() {
    fetch('/api/target-groups/')
        .then(res => res.json())
        .then(groups => {
            const select = document.getElementById('vulnGroupFilter');
            select.innerHTML = '<option value="">All Groups</option>';
            groups.forEach(group => {
                const option = document.createElement('option');
                option.value = group.id;
                option.textContent = group.name;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Error fetching groups:', error));
}

// Load vulnerabilities for selected target
window.loadTargetVulnerabilities = async function () {
    const select = document.getElementById('vulnTargetSelect');
    const targetId = select.value;

    if (!targetId) {
        // Hide filters, list, and details if no target selected
        document.getElementById('vulnFiltersCard').classList.add('hidden');
        document.getElementById('vulnListCard').classList.add('hidden');
        document.getElementById('vulnTargetDetailsCard').classList.add('hidden');
        return;
    }

    currentVulnTargetId = targetId;

    // Update title with target name
    const targetName = select.options[select.selectedIndex].text;
    const cleanName = targetName.split(' (')[0];
    document.getElementById('vulnListTitle').textContent = `Vulnerabilities - ${cleanName}`;

    // Show filters and list
    document.getElementById('vulnFiltersCard').classList.remove('hidden');
    document.getElementById('vulnListCard').classList.remove('hidden');
    document.getElementById('vulnTargetDetailsCard').classList.remove('hidden');

    // Fetch and populate target details
    try {
        // We need to fetch the target list again or find it if we stored it
        // For simplicity, we can fetch the specific target if we had an endpoint, 
        // but since we have the list in the dropdown, we can try to get info from there or fetch all targets
        const response = await fetch('/api/targets/');
        const targets = await response.json();
        const target = targets.find(t => t.id == targetId);

        if (target) {
            document.getElementById('vulnTargetName').textContent = target.name;
            document.getElementById('vulnTargetIP').textContent = target.ip_address;
            document.getElementById('vulnTargetDesc').textContent = target.description || 'No description provided';
        }
    } catch (error) {
        console.error('Error fetching target details:', error);
    }

    // Populate filter dropdowns
    populateVulnHosts();
    populateVulnGroups();

    // Load vulnerabilities
    await applyVulnFilters();
};

// Apply filters and fetch vulnerabilities
// Apply filters and fetch vulnerabilities
window.applyVulnFilters = async function () {
    const hostFilter = document.getElementById('vulnHostFilter').value;
    const groupFilter = document.getElementById('vulnGroupFilter').value;
    const severity = document.getElementById('vulnSeverityFilter').value;
    const status = document.getElementById('vulnStatusFilter').value;
    const search = document.getElementById('vulnSearchFilter').value;
    const serviceFilter = document.getElementById('vulnServiceFilter').value;

    // Build query params
    const params = new URLSearchParams();

    // Use host filter if selected, otherwise use current target
    if (hostFilter) {
        params.append('target_id', hostFilter);
    } else if (currentVulnTargetId) {
        params.append('target_id', currentVulnTargetId);
    }

    // Add group filter if selected
    if (groupFilter) {
        params.append('group_id', groupFilter);
    }

    if (severity) params.append('severity', severity);
    if (status) params.append('status', status);
    if (search) params.append('search', search);

    try {
        const response = await fetch(`/api/vulns/instances?${params}`);
        let vulnerabilities = await response.json();

        // Populate Service Filter if needed (and if we have results)
        // We do this BEFORE filtering by service so we see all available services for the current server-side filters
        populateServiceOptions(vulnerabilities);

        // Client-side filtering for Service
        if (serviceFilter) {
            vulnerabilities = vulnerabilities.filter(v => v.service === serviceFilter);
        }

        renderVulnerabilities(vulnerabilities);
    } catch (error) {
        console.error('Error fetching vulnerabilities:', error);
    }
};

// Helper to populate service options
function populateServiceOptions(vulnerabilities) {
    const select = document.getElementById('vulnServiceFilter');
    const currentSelection = select.value;

    // Extract unique services
    const services = [...new Set(vulnerabilities.map(v => v.service).filter(s => s))].sort();

    // Save current options to check if we need to update
    // If we just clear and append, we might lose the selection if the new list doesn't have it (which shouldn't happen if logic is correct)
    // But to avoid flickering, let's only update if the list is different or empty

    // For simplicity, let's rebuild but try to keep selection
    select.innerHTML = '<option value="">All Services</option>';

    services.forEach(service => {
        const option = document.createElement('option');
        option.value = service;
        option.textContent = service;
        if (service === currentSelection) {
            option.selected = true;
        }
        select.appendChild(option);
    });
}

// Clear all filters
window.clearVulnFilters = function () {
    document.getElementById('vulnHostFilter').value = '';
    document.getElementById('vulnGroupFilter').value = '';
    document.getElementById('vulnSeverityFilter').value = '';
    document.getElementById('vulnStatusFilter').value = 'open';
    document.getElementById('vulnSearchFilter').value = '';
    document.getElementById('vulnServiceFilter').value = '';
    applyVulnFilters();
};

// Render vulnerabilities in table
function renderVulnerabilities(vulnerabilities) {
    const vulnList = document.getElementById('vulnList');
    const vulnCount = document.getElementById('vulnCount');

    vulnCount.textContent = `${vulnerabilities.length} ${vulnerabilities.length === 1 ? 'vulnerability' : 'vulnerabilities'}`;

    // Update count in details card
    const detailsCount = document.getElementById('vulnTargetCount');
    if (detailsCount) {
        detailsCount.textContent = vulnerabilities.length;
    }

    if (vulnerabilities.length === 0) {
        vulnList.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                    No vulnerabilities found for this target with the current filters.
                </td>
            </tr>
        `;
        return;
    }

    vulnList.innerHTML = vulnerabilities.map(vuln => `
        <tr>
            <td>
                <strong>${vuln.vulnerability_name || 'Unknown'}</strong>
                ${vuln.cvss_score ? `<br><small style="color: var(--text-secondary);">Score: ${vuln.cvss_score}</small>` : ''}
            </td>
            <td>${getSeverityBadge(vuln.severity)}</td>
            <td>${vuln.cvss_score ? vuln.cvss_score.toFixed(1) : '-'}</td>
            <td>${vuln.port || '-'}${vuln.protocol ? `/${vuln.protocol}` : ''}</td>
            <td>${getVulnStatusBadge(vuln.status)}</td>
            <td>${vuln.detected_at ? new Date(vuln.detected_at).toLocaleDateString() : '-'}</td>
            <td>
                <button onclick="showVulnDetails(${vuln.id})" class="btn btn-secondary" style="padding: 0.5rem 1rem;">
                    <i class="fas fa-info-circle"></i> Details
                </button>
            </td>
        </tr>
    `).join('');
}

// Get severity badge HTML
function getSeverityBadge(severity) {
    const badges = {
        'Critical': '<span class="badge badge-error">Critical</span>',
        'High': '<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #F59E0B;">High</span>',
        'Medium': '<span class="badge badge-warning">Medium</span>',
        'Low': '<span class="badge badge-info">Low</span>',
        'Info': '<span class="badge">Info</span>'
    };
    return badges[severity] || `<span class="badge">${severity}</span>`;
}

// Get vulnerability status badge
function getVulnStatusBadge(status) {
    const badges = {
        'open': '<span class="badge badge-error">Open</span>',
        'fixed': '<span class="badge badge-success">Fixed</span>',
        'false_positive': '<span class="badge">False Positive</span>',
        'accepted_risk': '<span class="badge badge-warning">Accepted Risk</span>'
    };
    return badges[status] || `<span class="badge">${status}</span>`;
}

// Show vulnerability details (placeholder for future modal)
window.showVulnDetails = async function (vulnId) {
    try {
        console.log('Loading vulnerability details for ID:', vulnId);

        // Fetch full vulnerability details
        const response = await fetch(`/api/vulns/instances?target_id=${currentVulnTargetId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch vulnerabilities: ${response.status} ${response.statusText}`);
        }

        const vulnerabilities = await response.json();
        console.log('Fetched vulnerabilities:', vulnerabilities.length);

        // Find the specific vulnerability
        const vuln = vulnerabilities.find(v => v.id === vulnId);

        if (!vuln) {
            console.error('Vulnerability not found in list. Looking for ID:', vulnId);
            console.error('Available IDs:', vulnerabilities.map(v => v.id));
            alert('Vulnerability not found');
            return;
        }

        console.log('Found vulnerability:', vuln);

        // Fetch the full vulnerability definition for description and remediation
        console.log('Fetching vulnerability definition for ID:', vuln.vulnerability_id);
        const vulnDefResponse = await fetch(`/api/vulns/${vuln.vulnerability_id}`);
        if (!vulnDefResponse.ok) {
            throw new Error(`Failed to fetch vulnerability definition: ${vulnDefResponse.status}`);
        }

        const vulnDef = await vulnDefResponse.json();
        console.log('Fetched vulnerability definition:', vulnDef);

        // Populate modal
        const titleEl = document.getElementById('vulnDetailTitle');
        if (!titleEl) {
            throw new Error('Modal element vulnDetailTitle not found');
        }
        titleEl.textContent = vuln.vulnerability_name || 'Unknown Vulnerability';

        document.getElementById('vulnDetailCVE').textContent = vulnDef.cve_id ? `CVE: ${vulnDef.cve_id}` : '';

        // Severity and CVSS
        document.getElementById('vulnDetailSeverity').innerHTML = getSeverityBadge(vuln.severity);
        document.getElementById('vulnDetailCVSS').textContent = vuln.cvss_score ? vuln.cvss_score.toFixed(1) : 'N/A';
        document.getElementById('vulnDetailStatus').innerHTML = getVulnStatusBadge(vuln.status);
        document.getElementById('vulnDetailDetected').textContent = vuln.detected_at ?
            new Date(vuln.detected_at).toLocaleString() : 'Unknown';

        // Target and Port
        document.getElementById('vulnDetailTarget').textContent = vuln.target_name || 'Unknown';
        const portInfo = [];
        if (vuln.port) portInfo.push(`Port ${vuln.port}`);
        if (vuln.protocol) portInfo.push(vuln.protocol.toUpperCase());
        if (vuln.service) portInfo.push(vuln.service);
        document.getElementById('vulnDetailPort').textContent = portInfo.length > 0 ? portInfo.join(' / ') : 'N/A';

        // Description
        document.getElementById('vulnDetailDescription').textContent = vulnDef.description || 'No description available.';

        // Evidence (if available)
        if (vuln.evidence) {
            document.getElementById('vulnDetailEvidenceSection').style.display = 'block';
            document.getElementById('vulnDetailEvidence').textContent = vuln.evidence;
        } else {
            document.getElementById('vulnDetailEvidenceSection').style.display = 'none';
        }

        // Remediation (if available)
        if (vulnDef.remediation) {
            document.getElementById('vulnDetailRemediationSection').style.display = 'block';
            document.getElementById('vulnDetailRemediation').textContent = vulnDef.remediation;
        } else {
            document.getElementById('vulnDetailRemediationSection').style.display = 'none';
        }

        // Set instance ID and current status for update form
        document.getElementById('vulnDetailInstanceId').value = vuln.id;
        document.getElementById('vulnNewStatus').value = vuln.status;

        // Show modal
        const modal = document.getElementById('vulnDetailsModal');
        if (!modal) {
            throw new Error('Modal element vulnDetailsModal not found');
        }
        modal.classList.remove('hidden');

        // Reset tabs (if function exists)
        if (typeof switchVulnTab === 'function') {
            switchVulnTab('details');
        } else {
            console.warn('switchVulnTab function not found, skipping tab reset');
        }

        // Pre-fill exploit search if CVE exists
        const exploitSearchEl = document.getElementById('exploitSearchQuery');
        if (exploitSearchEl) {
            if (vulnDef.cve_id) {
                exploitSearchEl.value = vulnDef.cve_id;
            } else {
                exploitSearchEl.value = '';
            }
        }

        console.log('Vulnerability details loaded successfully');

    } catch (error) {
        console.error('Error fetching vulnerability details:', error);
        console.error('Error stack:', error.stack);
        alert(`Failed to load vulnerability details: ${error.message}`);
    }
};

// Close vulnerability details modal
window.closeVulnDetails = function () {
    document.getElementById('vulnDetailsModal').classList.add('hidden');
};

// Toggle false positive reason field
window.toggleFalsePositiveReason = function () {
    const status = document.getElementById('vulnNewStatus').value;
    const reasonGroup = document.getElementById('falsePositiveReasonGroup');

    if (status === 'false_positive') {
        reasonGroup.style.display = 'block';
    } else {
        reasonGroup.style.display = 'none';
    }
};

// Update vulnerability status
window.updateVulnStatus = async function (event) {
    event.preventDefault();

    const instanceId = document.getElementById('vulnDetailInstanceId').value;
    const newStatus = document.getElementById('vulnNewStatus').value;
    const falsePositiveReason = document.getElementById('vulnFalsePositiveReason').value;

    const data = {
        status: newStatus
    };

    if (newStatus === 'false_positive' && falsePositiveReason) {
        data.false_positive_reason = falsePositiveReason;
    }

    try {
        const response = await fetch(`/api/vulns/instances/${instanceId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert('Vulnerability status updated successfully!');
            closeVulnDetails();
            // Refresh the vulnerability list
            await applyVulnFilters();
        } else {
            const error = await response.json();
            alert(`Failed to update status: ${error.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error updating vulnerability status:', error);
        alert('Failed to update vulnerability status');
    }
};

// Trigger create ticket from vulnerability details - ONE-CLICK CREATION
window.triggerCreateTicket = async function () {
    const vulnId = document.getElementById('vulnDetailInstanceId').value;
    const vulnName = document.getElementById('vulnDetailTitle').textContent;
    const vulnCVE = document.getElementById('vulnDetailCVE').textContent;

    if (!vulnId) {
        alert('Vulnerability ID not found');
        return;
    }

    // Get vulnerability details for auto-population
    const severityElement = document.getElementById('vulnDetailSeverity');
    const targetElement = document.getElementById('vulnDetailTarget');
    const portElement = document.getElementById('vulnDetailPort');
    const remediationElement = document.getElementById('vulnDetailRemediation');
    const cvssElement = document.getElementById('vulnDetailCVSS');

    // Extract text content, handling badge HTML
    const severityText = severityElement.textContent.trim();
    const target = targetElement ? targetElement.textContent : 'Unknown';
    const port = portElement ? portElement.textContent : 'N/A';
    const remediation = remediationElement ? remediationElement.textContent : '';
    const cvss = cvssElement ? cvssElement.textContent : 'N/A';

    // Map severity to priority
    const priorityMap = {
        'Critical': 'high',
        'High': 'high',
        'Medium': 'medium',
        'Low': 'low',
        'Info': 'low'
    };
    const priority = priorityMap[severityText] || 'medium';

    // Build comprehensive description
    let description = `Remediation required for vulnerability found on ${target}\n\n`;
    description += `Vulnerability: ${vulnName}\n`;
    if (vulnCVE) description += `${vulnCVE}\n`;
    description += `Severity: ${severityText}\n`;
    description += `CVSS Score: ${cvss}\n`;
    description += `Port/Service: ${port}\n\n`;

    if (remediation && remediation !== 'No remediation available.') {
        description += `Remediation Steps:\n${remediation}`;
    } else {
        description += `Please review and remediate this vulnerability according to security best practices.`;
    }

    // Show loading state on button
    const button = document.getElementById('btnCreateTicketFromVuln') || event.target;
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Ticket...';

    try {
        // Create ticket via new endpoint
        const response = await fetch('/api/tickets/create-from-vuln', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: `Fix: ${vulnName}`,
                description: description,
                priority: priority,
                status: 'open',
                vuln_instance_id: parseInt(vulnId)
            })
        });

        if (response.ok) {
            const result = await response.json();

            // Show success state briefly
            button.innerHTML = '<i class="fas fa-check"></i> Created!';
            button.classList.remove('btn-warning');
            button.classList.add('btn-success');

            // Show success notification
            const ticketId = result.ticket_id;
            const ticketTitle = result.ticket.title;

            // Create a temporary success notification
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: var(--success-green);
                color: white;
                padding: 1rem 1.5rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                z-index: 3000;
                max-width: 400px;
                animation: slideIn 0.3s ease-out;
            `;
            notification.innerHTML = `
                <div style="display: flex; align-items: start; gap: 1rem;">
                    <i class="fas fa-check-circle" style="font-size: 1.5rem; margin-top: 0.25rem;"></i>
                    <div style="flex: 1;">
                        <strong style="display: block; margin-bottom: 0.5rem;">Ticket Created Successfully!</strong>
                        <div style="font-size: 0.875rem; opacity: 0.9;">
                            Ticket #${ticketId}: ${ticketTitle.substring(0, 50)}${ticketTitle.length > 50 ? '...' : ''}
                        </div>
                        <a href="#" onclick="event.preventDefault(); showSection('tickets'); document.getElementById('vulnDetailsModal').classList.add('hidden');" 
                           style="color: white; text-decoration: underline; font-size: 0.875rem; display: inline-block; margin-top: 0.5rem;">
                            View Tickets →
                        </a>
                    </div>
                    <button onclick="this.parentElement.parentElement.remove()" 
                            style="background: none; border: none; color: white; cursor: pointer; font-size: 1.25rem; padding: 0;">
                        ×
                    </button>
                </div>
            `;
            document.body.appendChild(notification);

            // Auto-remove notification after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.style.animation = 'slideOut 0.3s ease-out';
                    setTimeout(() => notification.remove(), 300);
                }
            }, 5000);

            // Reset button after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalText;
                button.disabled = false;
                button.classList.remove('btn-success');
                button.classList.add('btn-warning');
            }, 2000);

        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create ticket');
        }
    } catch (error) {
        console.error('Error creating ticket:', error);

        // Show error state
        button.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Failed';
        button.classList.remove('btn-warning');
        button.classList.add('btn-danger');

        alert(`Failed to create ticket: ${error.message}`);

        // Reset button after 2 seconds
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
            button.classList.remove('btn-danger');
            button.classList.add('btn-warning');
        }, 2000);
    }
};

// ========== Comments Management ==========

// Load comments for the current vulnerability
window.loadVulnComments = async function () {
    const vulnId = document.getElementById('vulnDetailInstanceId').value;
    if (!vulnId) return;

    try {
        const response = await fetch(`/api/collaboration/comments/vulnerability/${vulnId}`);
        const comments = await response.json();
        renderComments(comments);
    } catch (error) {
        console.error('Error fetching comments:', error);
    }
};

function renderComments(comments) {
    const list = document.getElementById('vulnCommentsList');
    if (!list) return;

    if (comments.length === 0) {
        list.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No comments yet.</p>';
        return;
    }

    list.innerHTML = comments.map(comment => `
        <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 0.5rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <strong style="color: var(--accent-cyan);">${comment.user_name}</strong>
                <span style="color: var(--text-secondary); font-size: 0.875rem;">${new Date(comment.created_at).toLocaleString()}</span>
            </div>
            <div style="color: var(--text-primary); white-space: pre-wrap;">${comment.text}</div>
        </div>
    `).join('');
}

// Add Comment
window.addVulnComment = async function (event) {
    event.preventDefault();
    const vulnId = document.getElementById('vulnDetailInstanceId').value;
    const text = document.getElementById('newCommentText').value;

    if (!text.trim()) return;

    try {
        const response = await fetch('/api/collaboration/comments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                resource_type: 'vulnerability',
                resource_id: parseInt(vulnId)
            })
        });

        if (response.ok) {
            document.getElementById('newCommentText').value = '';
            loadVulnComments(); // Refresh list
        } else {
            const error = await response.json();
            alert(`Failed to add comment: ${error.error}`);
        }
    } catch (error) {
        console.error('Error adding comment:', error);
        alert('Failed to add comment');
    }
};

// Hook into tab switching to load comments
window.switchVulnTab = function (tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) btn.classList.add('active');
    });

    // Show/hide content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    document.getElementById(`vulnTab-${tabName}`).classList.remove('hidden');

    // Load specific data
    if (tabName === 'comments') {
        loadVulnComments();
    }
};
