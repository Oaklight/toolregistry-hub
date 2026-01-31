/**
 * Tool Selector Frontend JavaScript
 * Handles the interactive functionality for the tool selector interface
 */

class ToolSelector {
    constructor() {
        this.tools = {};
        this.serverOnline = false;
        this.lastUpdate = null;
        this.statusPollingInterval = null;

        this.init();
    }

    async init() {
        console.log('Initializing Tool Selector...');
        this.setupEventListeners();
        await this.loadTools();
        this.startStatusPolling();
    }

    /**
     * Load tools from the API
     */
    async loadTools() {
        try {
            this.showLoading(true);
            this.updateStatus('正在加载工具列表...', 'info');

            const response = await fetch('/api/tools');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            this.tools = await response.json();
            this.renderToolsTable();
            this.updateCounts();
            this.updateStatus(`成功加载 ${Object.keys(this.tools).length} 个工具`, 'success');
            this.lastUpdate = new Date();
            this.updateLastUpdateTime();

        } catch (error) {
            console.error('Failed to load tools:', error);
            this.updateStatus('加载工具列表失败: ' + error.message, 'error');
            this.showEmptyState();
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Render the tools table
     */
    renderToolsTable() {
        const tbody = document.getElementById('tools-tbody');
        tbody.innerHTML = '';

        const toolsArray = Object.values(this.tools);

        if (toolsArray.length === 0) {
            this.showEmptyState();
            return;
        }

        // Hide empty state
        document.getElementById('empty-state').style.display = 'none';

        // Sort tools by name
        toolsArray.sort((a, b) => a.name.localeCompare(b.name));

        toolsArray.forEach(tool => {
            const row = this.createToolRow(tool);
            tbody.appendChild(row);
        });
    }

    /**
     * Create a table row for a tool
     */
    createToolRow(tool) {
        const row = document.createElement('tr');
        row.setAttribute('data-tool-id', tool.id);

        // Tool name
        const nameCell = document.createElement('td');
        nameCell.innerHTML = `
            <div style="font-weight: 600; color: #495057;">${this.escapeHtml(tool.name)}</div>
            <div style="font-size: 12px; color: #6c757d; margin-top: 2px;">${this.escapeHtml(tool.description)}</div>
        `;

        // API prefix
        const prefixCell = document.createElement('td');
        prefixCell.innerHTML = `<code>${this.escapeHtml(tool.prefix)}</code>`;

        // Tags
        const tagsCell = document.createElement('td');
        tagsCell.innerHTML = tool.tags.map(tag =>
            `<span class="tag">${this.escapeHtml(tag)}</span>`
        ).join('');

        // Endpoint count
        const endpointCell = document.createElement('td');
        endpointCell.innerHTML = `
            <span style="font-weight: 600;">${tool.endpoint_count}</span>
            <div style="font-size: 11px; color: #6c757d;">endpoints</div>
        `;

        // Module name
        const moduleCell = document.createElement('td');
        moduleCell.innerHTML = `<span class="module-name">${this.escapeHtml(tool.module_name.split('.').pop())}</span>`;

        // Status
        const statusCell = document.createElement('td');
        statusCell.innerHTML = `
            <span class="status-${tool.enabled ? 'enabled' : 'disabled'}">
                ${tool.enabled ? '✅ 启用' : '❌ 禁用'}
            </span>
        `;

        // Toggle switch
        const actionCell = document.createElement('td');
        const toggleId = `toggle-${tool.id}`;
        actionCell.innerHTML = `
            <label class="toggle-switch">
                <input type="checkbox" id="${toggleId}" ${tool.enabled ? 'checked' : ''}>
                <span class="slider"></span>
            </label>
        `;

        // Add event listener to toggle
        const toggleInput = actionCell.querySelector('input');
        toggleInput.addEventListener('change', (e) => {
            this.toggleTool(tool.id, e.target.checked);
        });

        row.appendChild(nameCell);
        row.appendChild(prefixCell);
        row.appendChild(tagsCell);
        row.appendChild(endpointCell);
        row.appendChild(moduleCell);
        row.appendChild(statusCell);
        row.appendChild(actionCell);

        return row;
    }

    /**
     * Toggle a tool's enabled state
     */
    async toggleTool(toolId, enabled) {
        const tool = this.tools[toolId];
        if (!tool) return;

        const toggleInput = document.getElementById(`toggle-${toolId}`);
        const originalState = tool.enabled;

        try {
            // Disable toggle during request
            toggleInput.disabled = true;

            this.updateStatus(`正在${enabled ? '启用' : '禁用'}工具 ${tool.name}...`, 'info');

            const response = await fetch(`/api/tools/${toolId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                // Update local state
                tool.enabled = enabled;

                // Update the status cell
                const row = document.querySelector(`tr[data-tool-id="${toolId}"]`);
                if (row) {
                    const statusCell = row.children[5]; // Status column
                    statusCell.innerHTML = `
                        <span class="status-${enabled ? 'enabled' : 'disabled'}">
                            ${enabled ? '✅ 启用' : '❌ 禁用'}
                        </span>
                    `;
                }

                this.updateCounts();
                this.updateStatus(`工具 ${tool.name} 已${enabled ? '启用' : '禁用'}`, 'success');
                this.showToast(`工具 ${tool.name} 已${enabled ? '启用' : '禁用'}`, 'success');

            } else {
                throw new Error(result.message || '操作失败');
            }

        } catch (error) {
            console.error('Toggle tool failed:', error);

            // Revert toggle state
            toggleInput.checked = originalState;
            tool.enabled = originalState;

            this.updateStatus(`切换工具 ${tool.name} 失败: ${error.message}`, 'error');
            this.showToast(`操作失败: ${error.message}`, 'error');

        } finally {
            toggleInput.disabled = false;
        }
    }

    /**
     * Reload the server
     */
    async reloadServer() {
        const reloadBtn = document.getElementById('reload-btn');
        const originalText = reloadBtn.innerHTML;

        try {
            reloadBtn.disabled = true;
            reloadBtn.innerHTML = '🔄 重新加载中...';

            this.updateStatus('正在重新加载服务器...', 'info');

            const response = await fetch('/api/server/reload', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                this.updateStatus(`服务器重新加载成功，发现 ${result.tools_discovered} 个工具`, 'success');
                this.showToast('服务器重新加载成功', 'success');

                // Reload tools list
                await this.loadTools();

            } else {
                throw new Error(result.message || '重新加载失败');
            }

        } catch (error) {
            console.error('Reload server failed:', error);
            this.updateStatus('重新加载服务器失败: ' + error.message, 'error');
            this.showToast('重新加载失败: ' + error.message, 'error');

        } finally {
            reloadBtn.disabled = false;
            reloadBtn.innerHTML = originalText;
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        document.getElementById('reload-btn').addEventListener('click', () => {
            this.reloadServer();
        });

        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadTools();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        e.preventDefault();
                        this.loadTools();
                        break;
                    case 'R':
                        e.preventDefault();
                        this.reloadServer();
                        break;
                }
            }
        });
    }

    /**
     * Start polling server status
     */
    startStatusPolling() {
        this.statusPollingInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/tools/status');
                this.updateServerStatus(response.ok);
            } catch (error) {
                this.updateServerStatus(false);
            }
        }, 5000);
    }

    /**
     * Update server status indicator
     */
    updateServerStatus(online) {
        this.serverOnline = online;
        const indicator = document.getElementById('server-status');
        indicator.className = `status-indicator ${online ? 'online' : 'offline'}`;
    }

    /**
     * Update status text
     */
    updateStatus(message, type = 'info') {
        const statusText = document.getElementById('status-text');
        statusText.textContent = message;
        statusText.className = type === 'error' ? 'error' : '';
    }

    /**
     * Update tool counts
     */
    updateCounts() {
        const toolsArray = Object.values(this.tools);
        const totalCount = toolsArray.length;
        const enabledCount = toolsArray.filter(tool => tool.enabled).length;

        document.getElementById('tools-count').textContent = `工具数: ${totalCount}`;
        document.getElementById('enabled-count').textContent = `已启用: ${enabledCount}`;
    }

    /**
     * Update last update time
     */
    updateLastUpdateTime() {
        if (this.lastUpdate) {
            const timeStr = this.lastUpdate.toLocaleTimeString('zh-CN');
            document.getElementById('last-update').textContent = timeStr;
        }
    }

    /**
     * Show/hide loading state
     */
    showLoading(show) {
        const loadingRow = document.querySelector('.loading-row');
        if (loadingRow) {
            loadingRow.style.display = show ? 'table-row' : 'none';
        }
    }

    /**
     * Show empty state
     */
    showEmptyState() {
        document.getElementById('tools-tbody').innerHTML = '';
        document.getElementById('empty-state').style.display = 'block';
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        container.appendChild(toast);

        // Auto remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Cleanup when page unloads
     */
    destroy() {
        if (this.statusPollingInterval) {
            clearInterval(this.statusPollingInterval);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.toolSelector = new ToolSelector();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.toolSelector) {
        window.toolSelector.destroy();
    }
});