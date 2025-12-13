// Asset Inventory Management

// Populate target dropdown for asset inventory
async function populateAssetTargets() {
    try {
        const response = await fetch('/api/targets/');
        const targets = await response.json();
        const select = document.getElementById('assetTargetSelect');

        if (!select) return;

        select.innerHTML = '<option value="">Select a target to view assets...</option>';
        targets.forEach(target => {
            const option = document.createElement('option');
            option.value = target.id;
            option.textContent = `${target.name} (${target.ip_address})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading asset targets:', error);
    }
}

// Load assets for selected target
async function loadTargetAssets() {
    const targetId = document.getElementById('assetTargetSelect').value;

    if (!targetId) {
        document.getElementById('osInfoCard').classList.add('hidden');
        document.getElementById('assetsListCard').classList.add('hidden');
        return;
    }

    try {
        const response = await fetch(`/api/assets/targets/${targetId}/assets`);
        const data = await response.json();

        // Show cards
        document.getElementById('osInfoCard').classList.remove('hidden');
        document.getElementById('assetsListCard').classList.remove('hidden');

        // Render OS information
        renderOSInfo(data.os, data.target);

        // Render services
        renderAssetServices(data.services);

    } catch (error) {
        console.error('Error loading assets:', error);
    }
}

// Render OS information
function renderOSInfo(osInfo, target) {
    const container = document.getElementById('osDetails');

    if (!osInfo || !osInfo.name) {
        container.innerHTML = `
            <div style="padding: 1rem; color: var(--text-secondary);">
                <i class="fas fa-info-circle"></i> No OS information detected yet. 
                Run a scan to detect the operating system.
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div>
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem;">OS NAME</div>
                <div style="font-size: 1.125rem; font-weight: 600; color: var(--text-primary);">${osInfo.name}</div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem;">CPE IDENTIFIER</div>
                <div style="font-size: 0.875rem; font-family: monospace; color: var(--accent-cyan);">
                    ${osInfo.cpe || 'Not available'}
                </div>
            </div>
            <div>
                <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem;">LAST DETECTED</div>
                <div style="font-size: 0.875rem; color: var(--text-primary);">
                    ${osInfo.last_detected ? new Date(osInfo.last_detected).toLocaleString() : 'Unknown'}
                </div>
            </div>
        </div>
    `;
}

// Render asset services
function renderAssetServices(services) {
    const tbody = document.getElementById('assetsList');

    if (!services || services.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: var(--text-secondary); padding: 2rem;">
                    No services discovered yet. Run a scan to discover services.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = services.map(asset => `
        <tr>
            <td><span class="badge badge-info">${asset.port}</span></td>
            <td>${asset.protocol || 'tcp'}</td>
            <td>${asset.service || '-'}</td>
            <td>${asset.product || '-'} ${asset.version || ''}</td>
            <td>
                ${asset.banner ? `
                    <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem; font-size: 0.75rem;" 
                            onclick="showBannerModal('${escapeHtml(asset.banner)}', ${asset.port})">
                        <i class="fas fa-eye"></i> View
                    </button>
                ` : '<span style="color: var(--text-muted);">-</span>'}
            </td>
            <td style="font-family: monospace; font-size: 0.75rem;">
                ${asset.cpe ? asset.cpe.substring(0, 40) + '...' : '-'}
            </td>
            <td style="font-size: 0.75rem; color: var(--text-secondary);">
                ${asset.last_seen ? new Date(asset.last_seen).toLocaleDateString() : '-'}
            </td>
        </tr>
    `).join('');

    // Update count
    document.getElementById('assetCount').textContent = `${services.length} services`;
}

// Show banner in modal
function showBannerModal(banner, port) {
    const modal = document.createElement('div');
    modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.9); z-index: 3000; display: flex; align-items: center; justify-content: center;';

    modal.innerHTML = `
        <div class="card" style="max-width: 800px; width: 90%; max-height: 80vh; overflow-y: auto;">
            <div class="card-header">
                <h3 class="card-title">Service Banner - Port ${port}</h3>
                <button onclick="this.closest('div[style*=fixed]').remove()" 
                        style="background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 1.5rem;">&times;</button>
            </div>
            <div class="log-output" style="max-height: 400px;">
                <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word; font-size: 0.875rem;">${banner}</pre>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// Refresh banners for target
async function refreshBanners() {
    const targetId = document.getElementById('assetTargetSelect').value;

    if (!targetId) {
        UI.toast('Please select a target first', 'warning');
        return;
    }

    await UI.asyncOperation(async () => {
        const response = await fetch(`/api/assets/targets/${targetId}/refresh-banners`, {
            method: 'POST'
        });

        const result = await response.json();
        UI.toast(`Banner refresh completed! ${result.banners_grabbed} banners grabbed.`, 'success');

        // Reload assets
        loadTargetAssets();
    }, 'Refreshing banners...');
}

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize asset inventory when section is shown
window.populateAssetTargets = populateAssetTargets;
window.loadTargetAssets = loadTargetAssets;
window.refreshBanners = refreshBanners;
window.showBannerModal = showBannerModal;
