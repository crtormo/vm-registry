/**
 * Network Scanner - Visualizador de Red con D3.js
 * Conexión WebSocket + Force-Directed Graph
 */
console.log('🌐 Network Scanner - Script cargado v20241229_v3_fixed');

// ============================================
// Configuración
// ============================================
const CONFIG = {
    API_URL: '',  // Ruta relativa, nginx hace proxy
    WS_URL: `ws://${window.location.host}/ws/live`,
    NODE_RADIUS: {
        gateway: 35,
        server: 28,
        default: 22,
        virtual: 15
    },
    UPDATE_INTERVAL: 30000
};

const DEVICE_CONFIG = {
    router: { icon: '🌐', color: '#22c55e', label: 'Router' },
    server: { icon: '🖥️', color: '#3b82f6', label: 'Servidor' },
    vm: { icon: '📦', color: '#8b5cf6', label: 'VM' },
    container: { icon: '🐳', color: '#a855f7', label: 'Container' },
    pc: { icon: '💻', color: '#06b6d4', label: 'PC' },
    mobile: { icon: '📱', color: '#f59e0b', label: 'Móvil' },
    nas: { icon: '💾', color: '#ec4899', label: 'NAS' },
    iot: { icon: '🔌', color: '#14b8a6', label: 'IoT' },
    lighting: { icon: '💡', color: '#fbbf24', label: 'Iluminación' },
    printer: { icon: '🖨️', color: '#f97316', label: 'Impresora' },
    unknown: { icon: '❓', color: '#64748b', label: 'Desconocido' }
};

// ============================================
// Estado Global
// ============================================
let state = {
    devices: [],
    networkInfo: null,
    isScanning: false,
    isConnected: false,
    simulation: null,
    ws: null
};

// ============================================
// Elementos DOM
// ============================================
const elements = {
    networkGraph: document.getElementById('networkGraph'),
    networkAddress: document.getElementById('networkAddress'),
    totalDevices: document.getElementById('totalDevices'),
    scanTime: document.getElementById('scanTime'),
    lastScan: document.getElementById('lastScan'),
    connectionStatus: document.getElementById('connectionStatus'),
    scanningOverlay: document.getElementById('scanningOverlay'),
    tooltip: document.getElementById('tooltip'),
    devicePanel: document.getElementById('devicePanel'),
    panelTitle: document.getElementById('panelTitle'),
    panelContent: document.getElementById('panelContent'),
    btnStartScan: document.getElementById('btnStartScan'),
    scanTypeSelect: document.getElementById('scanTypeSelect'),
    btnClosePanel: document.getElementById('btnClosePanel')
};

// ============================================
// Inicialización
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    connectWebSocket();
    loadInitialData();

    if (elements.btnStartScan) {
        elements.btnStartScan.addEventListener('click', () => {
            const scanType = elements.scanTypeSelect ? elements.scanTypeSelect.value : 'quick';
            console.log('[UI] Botón Escanear clickeado, tipo:', scanType);
            triggerScan(scanType);
        });
    }

    if (elements.btnClosePanel) {
        elements.btnClosePanel.addEventListener('click', closeDevicePanel);
    }
});

async function loadInitialData() {
    try {
        const response = await fetch(`${CONFIG.API_URL}/api/devices`);
        const devices = await response.json();

        const netResponse = await fetch(`${CONFIG.API_URL}/api/network`);
        const network = await netResponse.json();

        updateFromScanResult({
            devices: devices,
            network: network.network,
            gateway: network.gateway,
            total_devices: devices.length,
            scan_duration_ms: 0,
            timestamp: new Date().toISOString()
        });
    } catch (e) {
        console.error("Error cargando datos iniciales:", e);
    }
}

// ============================================
// WebSocket Connection
// ============================================
function connectWebSocket() {
    console.log('[WS] Conectando a', CONFIG.WS_URL);
    state.ws = new WebSocket(CONFIG.WS_URL);

    state.ws.onopen = () => {
        console.log('[WS] Conectado');
        updateConnectionStatus(true);
    };

    state.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
    };

    state.ws.onclose = () => {
        console.log('[WS] Desconectado');
        updateConnectionStatus(false);
        setTimeout(connectWebSocket, 3000);
    };

    state.ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        updateConnectionStatus(false);
    };
}

function handleWebSocketMessage(message) {
    if (message.type === 'initial_state' || message.type === 'scan_complete' || message.type === 'scan_update') {
        updateFromScanResult(message.data);
        hideScanning();
    } else if (message.type === 'scan_starting') {
        showScanning();
    }
}

function updateConnectionStatus(connected) {
    state.isConnected = connected;
    const indicator = elements.connectionStatus.querySelector('.status-indicator');
    const label = elements.connectionStatus.querySelector('.stat-label');

    if (connected) {
        indicator.classList.remove('disconnected');
        indicator.classList.add('connected');
        label.textContent = 'Conectado';
    } else {
        indicator.classList.remove('connected');
        indicator.classList.add('disconnected');
        label.textContent = 'Desconectado';
    }
}

// ============================================
// Scan Functions
// ============================================
async function triggerScan(scanType = 'quick') {
    if (state.isScanning) return;
    showScanning();

    const useNmap = scanType !== 'quick';

    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ action: 'scan', use_nmap: useNmap, scan_type: scanType }));
    } else {
        try {
            const response = await fetch(`${CONFIG.API_URL}/api/scan?use_nmap=${useNmap}&scan_type=${scanType}`);
            const data = await response.json();
            updateFromScanResult(data);
        } catch (error) {
            console.error('[Scan] Error:', error);
        } finally {
            hideScanning();
        }
    }
}

function showScanning() {
    state.isScanning = true;
    if (elements.scanningOverlay) elements.scanningOverlay.classList.add('active');
    if (elements.btnStartScan) elements.btnStartScan.disabled = true;
}

function hideScanning() {
    state.isScanning = false;
    if (elements.scanningOverlay) elements.scanningOverlay.classList.remove('active');
    if (elements.btnStartScan) elements.btnStartScan.disabled = false;
}

// ============================================
// Update UI
// ============================================
function updateFromScanResult(result) {
    state.devices = result.devices || [];
    state.networkInfo = { network: result.network, gateway: result.gateway };

    elements.networkAddress.textContent = result.network;
    elements.totalDevices.textContent = result.total_devices;
    elements.scanTime.textContent = `${result.scan_duration_ms}ms`;
    elements.lastScan.textContent = new Date(result.timestamp).toLocaleTimeString('es-ES');

    renderNetwork();
}

// ============================================
// D3.js Network Visualization
// ============================================
function renderNetwork() {
    const svg = d3.select('#networkGraph');
    const container = elements.networkGraph.parentElement;
    const width = container.clientWidth;
    const height = container.clientHeight;

    svg.selectAll('*').remove();

    if (state.devices.length === 0) {
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height / 2)
            .attr('text-anchor', 'middle')
            .attr('fill', '#64748b')
            .text('No hay dispositivos. Ejecuta un escaneo.');
        return;
    }

    const numDevices = state.devices.length;
    const angleStep = (2 * Math.PI) / Math.max(numDevices - 1, 1);
    const circleRadius = Math.max(250, numDevices * 20);

    const nodes = state.devices.map((d, i) => {
        const isGateway = d.is_gateway;
        const angle = i * angleStep;
        const x = isGateway ? 0 : circleRadius * Math.cos(angle);
        const y = isGateway ? 0 : circleRadius * Math.sin(angle);

        return {
            id: d.ip,
            ...d,
            x: x,
            y: y,
            radius: isGateway ? CONFIG.NODE_RADIUS.gateway :
                d.is_virtual ? CONFIG.NODE_RADIUS.virtual :
                    d.device_type === 'server' ? CONFIG.NODE_RADIUS.server :
                        CONFIG.NODE_RADIUS.default
        };
    });

    const gateway = nodes.find(n => n.is_gateway);
    const links = [];

    nodes.forEach(n => {
        if (n.is_gateway) return;

        let sourceId = gateway ? gateway.id : null;

        // Si tiene un padre definido (ej: HA Server), conectar a él
        if (n.parent) {
            const parentNode = nodes.find(p => p.ip === n.parent);
            if (parentNode) {
                sourceId = parentNode.id;
            }
        }

        if (sourceId) {
            links.push({ source: sourceId, target: n.id });
        }
    });

    const g = svg.append('g');

    const zoom = d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => g.attr('transform', event.transform));

    svg.call(zoom);
    svg.call(zoom.transform, d3.zoomIdentity.translate(width / 2, height / 2));

    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('class', 'link')
        .attr('stroke', '#334155')
        .attr('stroke-width', 1.5)
        .attr('opacity', 0.6);

    const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr('class', d => `node ${d.is_gateway ? 'gateway' : ''}`)
        .style('cursor', 'pointer')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended))
        .on('click', showDevicePanel);

    node.append('circle')
        .attr('r', d => d.radius)
        .attr('fill', d => {
            // Color especial para luces encendidas en HA
            if (d.is_virtual && d.ha_data && (d.ha_data.state === 'on' || d.ha_data.state === 'playing')) {
                return '#fbbf24'; // Dorado/Amarillo
            }
            return getDeviceColor(d.device_type);
        })
        .attr('stroke', d => d.is_virtual ? 'rgba(255,255,255,0.3)' : '#fff')
        .attr('stroke-width', d => d.is_virtual ? 1 : 2);

    node.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '.3em')
        .text(d => getDeviceIcon(d.device_type, d.ha_data, d.is_virtual))
        .style('font-size', d => d.radius + 'px');

    node.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', d => d.radius + 16)
        .text(d => d.hostname || d.ip.split('.').pop())
        .attr('fill', '#e2e8f0')
        .style('font-size', '12px');

    state.simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(100).strength(0.1))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('collision', d3.forceCollide().radius(d => d.radius + 20).strength(1));

    state.simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

function dragstarted(event, d) {
    if (!event.active) state.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) state.simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

function getDeviceColor(type) {
    const config = DEVICE_CONFIG[type] || DEVICE_CONFIG.unknown;
    return config.color;
}

function getDeviceIcon(type, ha_data = null, is_virtual = false) {
    if (is_virtual && ha_data) {
        const eid = ha_data.entity_id || '';
        if (eid.startsWith('light.')) return '💡';
        if (eid.startsWith('switch.')) return '🔌';
        if (eid.startsWith('media_player.')) return '📺';
        if (eid.startsWith('climate.')) return '🌡️';
    }
    const config = DEVICE_CONFIG[type] || DEVICE_CONFIG.unknown;
    return config.icon;
}

// ============================================
// Device Panel
// ============================================
function showDevicePanel(event, d) {
    // Si d viene del evento click de D3, es el datum. Si llamamos manualmente, es el objeto.
    const data = d.ip ? d : event;

    // Buscar configuración
    const config = DEVICE_CONFIG[data.device_type] || DEVICE_CONFIG.unknown;

    elements.panelTitle.innerHTML = `${config.icon} ${data.hostname || data.ip}`;
    elements.panelContent.innerHTML = `
        <div class="panel-section">
            <h3>Información</h3>
            <p><strong>IP:</strong> ${data.ip}</p>
            <p><strong>MAC:</strong> ${data.mac || 'N/A'}</p>
            <p><strong>Vendor:</strong> ${data.vendor || 'N/A'}</p>
            <p><strong>Tipo:</strong> ${data.device_type}</p>
            
            ${data.proxmox_data ? `
                <div style="margin-top: 10px; padding: 10px; border: 1px solid #d97706; border-radius: 6px; background: rgba(217, 119, 6, 0.1);">
                    <h4 style="margin: 0 0 5px 0; color: #fbbf24; font-size: 14px;">📦 Proxmox Virtualization</h4>
                    <p style="margin: 3px 0"><strong>VMID:</strong> ${data.proxmox_data.vmid}</p>
                    <p style="margin: 3px 0"><strong>Status:</strong> <span class="badge ${data.proxmox_data.status === 'running' ? 'bg-success' : 'bg-secondary'}">${data.proxmox_data.status}</span></p>
                    <p style="margin: 3px 0"><strong>Node:</strong> ${data.proxmox_data.node}</p>
                </div>
            ` : ''}

            ${data.ha_data ? `
                <div style="margin-top: 10px; padding: 10px; border: 1px solid #0ea5e9; border-radius: 6px; background: rgba(14, 165, 233, 0.1);">
                    <h4 style="margin: 0 0 5px 0; color: #38bdf8; font-size: 14px;">🏠 Home Assistant</h4>
                    <p style="margin: 3px 0"><strong>ID:</strong> <code style="font-size: 0.8em">${data.ha_data.entity_id}</code></p>
                    <p style="margin: 3px 0"><strong>Estado:</strong> <b>${data.ha_data.state} ${data.ha_data.unit || ''}</b></p>
                    ${data.ha_data.battery ? `<p style="margin: 3px 0"><strong>🔋 Batería:</strong> ${data.ha_data.battery}%</p>` : ''}
                </div>
            ` : ''}
        </div>
        <div class="panel-section">
            <h3>Acciones</h3>
            <div style="display: grid; gap: 10px;">
                 <button class="btn btn-secondary" onclick="window.open('http://${data.ip}', '_blank')">🌐 Abrir HTTP</button>
                 <button class="btn btn-secondary" onclick="deepScan('${data.ip}')">🔍 Escaneo Profundo</button>
                 <button class="btn btn-secondary" style="border-color: #f59e0b; color: #f59e0b;" onclick="wakeDevice('${data.ip}')">⚡ Wake-on-LAN</button>
                 <button class="btn btn-secondary" onclick="editDevice('${data.ip}')">✏️ Editar</button>
            </div>
        </div>
        <div id="deepScanResults"></div>
    `;

    elements.devicePanel.classList.add('open');
}

function closeDevicePanel() {
    elements.devicePanel.classList.remove('open');
}

async function deepScan(ip) {
    const resultsDiv = document.getElementById('deepScanResults');
    resultsDiv.innerHTML = '<p>Escaneando puertos...</p>';

    try {
        // Usamos standard scan para el deep scan
        const response = await fetch(`${CONFIG.API_URL}/api/devices/${ip}/deep-scan?scan_type=standard`);
        const data = await response.json();

        if (data.error) {
            resultsDiv.innerHTML = `<p style="color:red">Error: ${data.error}</p>`;
            return;
        }

        const ports = data.ports || [];
        if (ports.length === 0) {
            resultsDiv.innerHTML = '<p>No se encontraron puertos abiertos.</p>';
            return;
        }

        const portsList = ports.map(p =>
            `<li><strong>${p.port}/${p.protocol}</strong>: ${p.service} ${p.product || ''}</li>`
        ).join('');

        resultsDiv.innerHTML = `
            <h4>Puertos Abiertos (${ports.length})</h4>
            <ul>${portsList}</ul>
            ${data.os && data.os.length ? `<p><strong>OS:</strong> ${data.os[0].name} (${data.os[0].accuracy}%)</p>` : ''}
        `;

    } catch (e) {
        resultsDiv.innerHTML = `<p style="color:red">Error de conexión</p>`;
    }
}

// Funciones añadidas por dashboard v2

async function wakeDevice(ip) {
    if (!confirm('¿Enviar paquete Wake-on-LAN a ' + ip + '?')) return;

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/devices/${ip}/wake`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            alert('Paquete mágico enviado a ' + ip);
        } else {
            alert('Error: ' + (data.error || 'Fallo desconocido'));
        }
    } catch (e) {
        console.error(e);
        alert('Error de conexión');
    }
}

async function editDevice(ip) {
    const newName = prompt("Nuevo nombre (deja vacío para no cambiar):");

    if (newName === null) return;

    const updates = {};
    if (newName) updates.custom_name = newName;

    if (Object.keys(updates).length === 0) return;

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/devices/${ip}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });

        if (response.ok) {
            triggerScan('quick');
            closeDevicePanel();
        } else {
            alert('Error guardando cambios');
        }
    } catch (e) {
        console.error(e);
        alert('Error conectando al servidor');
    }
}

// ============================================
// Vistas y Navegación
// ============================================

window.switchView = function (viewName) {
    document.querySelectorAll('.nav-tab').forEach(t => {
        t.classList.toggle('active', t.dataset.view === viewName);
    });

    const graphView = document.getElementById('graphView');
    const inventoryView = document.getElementById('inventoryView');

    if (graphView && inventoryView) {
        graphView.style.display = viewName === 'graph' ? 'block' : 'none';
        inventoryView.style.display = viewName === 'inventory' ? 'block' : 'none';
    }

    if (viewName === 'inventory') {
        renderInventory();
    }
}

function renderInventory() {
    const grid = document.getElementById('inventoryGrid');
    if (!grid) return;
    grid.innerHTML = '';

    // Get filter values
    const searchInput = document.getElementById('inventorySearch');
    const search = searchInput ? searchInput.value.toLowerCase() : '';
    const filterType = document.getElementById('inventoryFilter').value;

    const filtered = state.devices.filter(d => {
        const hostname = (d.hostname || '').toLowerCase();
        const vendor = (d.vendor || '').toLowerCase();
        
        // Search filter
        if (search && !hostname.includes(search) && !d.ip.includes(search) && !vendor.includes(search)) return false;

        // Type filter
        if (filterType === 'online' && !d.is_online) return false;
        if (filterType === 'offline' && d.is_online) return false;
        if (filterType === 'rogue' && !d.is_rogue) return false;
        if (filterType === 'documented' && !d.registry_name) return false;
        if (filterType === 'critical' && !d.is_critical) return false; // assuming is_critical might exist in ha_data or proxmox_data

        return true;
    });

    // Update statistics
    const stats = {
        total: state.devices.length,
        online: state.devices.filter(d => d.is_online).length,
        documented: state.devices.filter(d => d.registry_name).length,
        rogue: state.devices.filter(d => d.is_rogue).length
    };

    if (document.getElementById('invTotal')) document.getElementById('invTotal').textContent = stats.total;
    if (document.getElementById('invOnline')) document.getElementById('invOnline').textContent = stats.online;
    if (document.getElementById('invDoc')) document.getElementById('invDoc').textContent = stats.documented;
    if (document.getElementById('invRogue')) document.getElementById('invRogue').textContent = stats.rogue;

    filtered.forEach(d => {
        const div = document.createElement('div');
        div.className = `inventory-card ${d.is_online ? 'online' : 'offline'}`;
        div.onclick = function () { showDevicePanel(null, d); };

        let icon = getDeviceIcon(d.device_type, d.ha_data, d.is_virtual);
        
        let tags = '';
        if (d.registry_name) tags += '<span class="tag tag-blue">📋 Documentado</span>';
        if (d.is_rogue) tags += '<span class="tag tag-yellow">⚠️ Rogue</span>';
        if (d.is_gateway) tags += '<span class="tag tag-purple">🌐 Gateway</span>';
        if (!d.is_online) tags += '<span class="tag tag-red">🔴 Offline</span>';

        div.innerHTML = `
            <div class="inv-header">
                <div class="inv-title">
                    <span class="status-dot ${d.is_online ? 'online' : 'offline'}"></span>
                    ${icon} ${d.hostname || d.ip}
                </div>
                <div class="inv-tags">${tags}</div>
            </div>
            <div class="inv-details">
                <div class="inv-row"><span>IP:</span> <strong>${d.ip}</strong></div>
                <div class="inv-row"><span>MAC:</span> <code>${d.mac || 'N/A'}</code></div>
                <div class="inv-row"><span>Vendor:</span> ${d.vendor || 'Desconocido'}</div>
                ${d.ha_data ? `<div class="inv-row"><span>HA:</span> <small>${d.ha_data.entity_id}</small></div>` : ''}
            </div>
            <div class="inv-actions">
                 <button class="btn btn-sm" onclick="event.stopPropagation(); wakeDevice('${d.ip}')">⚡ WOL</button>
                 <button class="btn btn-sm" onclick="event.stopPropagation(); window.open('http://${d.ip}', '_blank')">🌐 Web</button>
            </div>
        `;
        grid.appendChild(div);
    });
}

// Hook up event listeners
const invSearch = document.getElementById('inventorySearch');
if (invSearch) invSearch.addEventListener('input', renderInventory);

const invFilter = document.getElementById('inventoryFilter');
if (invFilter) invFilter.addEventListener('change', renderInventory);

// Fix Initial View
document.addEventListener('DOMContentLoaded', () => {
    switchView('graph');
});


// Lógica de Terminal Hacker
const terminal = {
    panel: document.getElementById('terminalPanel'),
    log: document.getElementById('terminalLog'),
    input: document.getElementById('terminalInput'),
    toggle: document.getElementById('btnToggleTerminal'),
    stats: {
        hosts: document.getElementById('termDeviceCount'),
        ports: document.getElementById('termPortsOpen'),
        alerts: document.getElementById('termAlerts'),
        uptime: document.getElementById('termUptime')
    },
    canvas: document.getElementById('activityGraph')
};

if (terminal.toggle) {
    terminal.toggle.addEventListener('click', () => {
        terminal.panel.classList.toggle('open');
        if (terminal.panel.classList.contains('open')) {
            terminal.input.focus();
            updateTerminalStats();
        }
    });
}

if (terminal.input) {
    terminal.input.addEventListener('keydown', async (e) => {
        if (e.key === 'Enter') {
            const cmd = terminal.input.value.trim();
            if (!cmd) return;

            terminal.input.value = '';
            addLog(`> ${cmd}`, 'cmd');

            if (cmd === 'clear') {
                terminal.log.innerHTML = '';
                return;
            }

            try {
                const response = await fetch(`${CONFIG.API_URL}/api/terminal/command`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd })
                });
                const data = await response.json();
                addLog(data.output, data.status);
            } catch (err) {
                addLog(`Error: ${err.message}`, 'error');
            }
        }
    });
}

function addLog(text, type = 'info') {
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    const time = new Date().toLocaleTimeString();
    line.innerHTML = `<span class="log-time">${time}</span> <span class="log-${type}">${text.replace(/\n/g, '<br>')}</span>`;
    terminal.log.appendChild(line);
    terminal.log.scrollTop = terminal.log.scrollHeight;
}

async function updateTerminalStats() {
    try {
        const response = await fetch(`${CONFIG.API_URL}/api/terminal/stats`);
        const stats = await response.json();

        if (terminal.stats.hosts) terminal.stats.hosts.textContent = stats.hosts;
        if (terminal.stats.ports) terminal.stats.ports.textContent = stats.ports;
        if (terminal.stats.alerts) {
            terminal.stats.alerts.textContent = stats.alerts;
            const badge = document.getElementById('alertBadge');
            if (badge) {
                badge.textContent = stats.alerts;
                badge.style.display = stats.alerts > 0 ? 'flex' : 'none';
            }
        }
        if (terminal.stats.uptime) terminal.stats.uptime.textContent = stats.uptime;

        if (stats.activity) drawActivity(stats.activity);

    } catch (e) {
        console.error("Error stats terminal:", e);
    }
}

function drawActivity(data) {
    if (!terminal.canvas) return;
    const ctx = terminal.canvas.getContext('2d');
    const w = terminal.canvas.width;
    const h = terminal.canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (data.length < 2) return;

    ctx.beginPath();
    ctx.strokeStyle = '#22c55e';
    ctx.lineWidth = 2;
    ctx.setLineDash([]);

    const step = w / (data.length - 1);
    const max = Math.max(...data, 10);

    data.forEach((val, i) => {
        const x = i * step;
        const y = h - (val / max) * h * 0.8;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    ctx.stroke();

    // Fill area
    ctx.lineTo(w, h);
    ctx.lineTo(0, h);
    ctx.fillStyle = 'rgba(34, 197, 94, 0.1)';
    ctx.fill();
}

// Iniciar actualizaciones periódicas
setInterval(updateTerminalStats, 10000);
updateTerminalStats();

// Lógica de Alertas (Simple)
const btnAlerts = document.getElementById('btnAlerts');
if (btnAlerts) {
    btnAlerts.addEventListener('click', async () => {
        try {
            const res = await fetch(CONFIG.API_URL + '/api/alerts?unread_only=true');
            const data = await res.json();
            if (data.alerts && data.alerts.length > 0) {
                let msg = data.alerts.map(a => `[${a.timestamp}] ${a.message}`).join('\n');
                alert("Últimas Alertas:\n" + msg);
                // Mark read
                const ids = data.alerts.map(a => a.id);
                await fetch(CONFIG.API_URL + '/api/alerts/read', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(ids)
                });
                document.getElementById('alertBadge').style.display = 'none';
            } else {
                alert('No hay alertas nuevas.');
            }
        } catch (e) { console.error(e); }
    });

