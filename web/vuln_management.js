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

// Load vulnerabilities for selected target
window.loadTargetVulnerabilities = async function () {
    const targetId = document.getElementById('vulnTargetSelect').value;

    if (!targetId) {
        // Hide filters and list if no target selected
        document.getElementById('vulnFiltersCard').classList.add('hidden');
        document.getElementById('vulnListCard').classList.add('hidden');
        return;
    }

    currentVulnTargetId = targetId;

    // Show filters and list
    document.getElementById('vulnFiltersCard').classList.remove('hidden');
    document.getElementById('vulnListCard').classList.remove('hidden');

    // Load vulnerabilities
    await applyVulnFilters();
};

// Apply filters and fetch vulnerabilities
window.applyVulnFilters = async function () {
    if (!currentVulnTargetId) return;

    const severity = document.getElementById('vulnSeverityFilter').value;
    const status = document.getElementById('vulnStatusFilter').value;
    const search = document.getElementById('vulnSearchFilter').value;

    // Build query params
    const params = new URLSearchParams({
        target_id: currentVulnTargetId
    });

    if (severity) params.append('severity', severity);
    if (status) params.append('status', status);
    if (search) params.append('search', search);

    try {
        const response = await fetch(`/api/vulns/instances?${params}`);
        const vulnerabilities = await response.json();
        renderVulnerabilities(vulnerabilities);
    } catch (error) {
        console.error('Error fetching vulnerabilities:', error);
    }
};

// Clear all filters
window.clearVulnFilters = function () {
    document.getElementById('vulnSeverityFilter').value = '';
    document.getElementById('vulnStatusFilter').value = 'open';
    document.getElementById('vulnSearchFilter').value = '';
    applyVulnFilters();
};

// Render vulnerabilities in table
function renderVulnerabilities(vulnerabilities) {
    const vulnList = document.getElementById('vulnList');
    const vulnCount = document.getElementById('vulnCount');

    vulnCount.textContent = `${vulnerabilities.length} ${vulnerabilities.length === 1 ? 'vulnerability' : 'vulnerabilities'}`;

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
        // Fetch full vulnerability details
        const response = await fetch(`/api/vulns/instances?target_id=${currentVulnTargetId}`);
        const vulnerabilities = await response.json();

        // Find the specific vulnerability
        const vuln = vulnerabilities.find(v => v.id === vulnId);

        if (!vuln) {
            alert('Vulnerability not found');
            return;
        }

        // Fetch the full vulnerability definition for description and remediation
        const vulnDefResponse = await fetch(`/api/vulns/${vuln.vulnerability_id}`);
        const vulnDef = await vulnDefResponse.json();

        // Populate modal
        document.getElementById('vulnDetailTitle').textContent = vuln.vulnerability_name || 'Unknown Vulnerability';
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
        document.getElementById('vulnDetailsModal').classList.remove('hidden');

    } catch (error) {
        console.error('Error fetching vulnerability details:', error);
        alert('Failed to load vulnerability details');
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

// Trigger create ticket from vulnerability details
window.triggerCreateTicket = function () {
    const vulnId = document.getElementById('vulnDetailInstanceId').value;
    const vulnName = document.getElementById('vulnDetailTitle').textContent;

    if (vulnId && typeof createTicketFromVuln === 'function') {
        closeVulnDetails();
        createTicketFromVuln(vulnId, vulnName);
    } else {
        console.error('Create ticket function not available or vuln ID missing');
    }
};
