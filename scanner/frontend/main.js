/**
 * Network Scanner - Visualizador de Red con D3.js
 * Conexión WebSocket + Force-Directed Graph
 */
console.log('🌐 Network Scanner - Script cargado v20241229_stable');

// ============================================
// Configuración
// ============================================
const CONFIG = {
    // Usar rutas relativas para pasar por el proxy nginx
    API_URL: '',  // Ruta relativa, nginx hace proxy a backend
    WS_URL: `ws://${window.location.host}/ws/live`,
    NODE_RADIUS: {
        gateway: 35,
        server: 28,
        default: 22
    },
    UPDATE_INTERVAL: 30000
};

// Iconos y colores por tipo de dispositivo
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
    ws: null,
    alerts: [],
    unreadAlerts: 0,
    searchQuery: '',
    filterType: 'all',
    filterGroup: 'all',
    layoutMode: 'force'  // 'force' or 'hierarchy'
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
    btnClosePanel: document.getElementById('btnClosePanel'),
    // New controls
    searchInput: document.getElementById('searchInput'),
    filterType: document.getElementById('filterType'),
    btnExport: document.getElementById('btnExport'),
    btnTheme: document.getElementById('btnTheme'),
    btnAlerts: document.getElementById('btnAlerts'),
    alertBadge: document.getElementById('alertBadge'),
    layoutMode: document.getElementById('layoutMode')
};

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
        // Reconectar después de 3 segundos
        setTimeout(connectWebSocket, 3000);
    };

    state.ws.onerror = (error) => {
        console.error('[WS] Error:', error);
        updateConnectionStatus(false);
    };
}

function handleWebSocketMessage(message) {
    console.log('[WS] Mensaje:', message.type);

    switch (message.type) {
        case 'initial_state':
        case 'scan_complete':
        case 'scan_update':
            updateFromScanResult(message.data);
            hideScanning();
            break;
        case 'scan_starting':
            showScanning();
            break;
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

    console.log('[Scan] Iniciando escaneo tipo:', scanType);
    showScanning();

    // Log en terminal
    if (typeof termLog === 'function') {
        termLog('SCAN', `Iniciando escaneo ${scanType}...`, 'scan');
    }

    const useNmap = scanType !== 'quick';

    // Si WebSocket está conectado, usar ese canal
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify({ action: 'scan', use_nmap: useNmap, scan_type: scanType }));
    } else {
        // Fallback a REST API
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
// Update UI from Scan Result
// ============================================
function updateFromScanResult(result) {
    state.devices = result.devices || [];
    state.networkInfo = {
        network: result.network,
        gateway: result.gateway
    };

    // Update stats
    elements.networkAddress.textContent = result.network;
    elements.totalDevices.textContent = result.total_devices;
    elements.scanTime.textContent = `${result.scan_duration_ms}ms`;
    elements.lastScan.textContent = new Date(result.timestamp).toLocaleTimeString('es-ES');

    // Update visualization
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

    // Clear previous
    svg.selectAll('*').remove();

    // Get filtered devices (uses search and filter state)
    const devices = typeof getFilteredDevices === 'function' ? getFilteredDevices() : state.devices;

    if (devices.length === 0) {
        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height / 2)
            .attr('text-anchor', 'middle')
            .attr('fill', '#64748b')
            .text(state.devices.length > 0 ? 'Sin resultados para el filtro.' : 'No hay dispositivos. Ejecuta un escaneo.');
        return;
    }

    // Preparar datos para D3 con posiciones iniciales en círculo
    const numDevices = devices.length;
    const angleStep = (2 * Math.PI) / Math.max(numDevices - 1, 1);
    const circleRadius = Math.max(250, numDevices * 20); // Radio grande: 20px por dispositivo

    const nodes = devices.map((d, i) => {
        const isGateway = d.is_gateway;
        // Gateway en el centro, otros en círculo
        const angle = i * angleStep;
        const x = isGateway ? 0 : circleRadius * Math.cos(angle);
        const y = isGateway ? 0 : circleRadius * Math.sin(angle);

        return {
            id: d.ip,
            ...d,
            x: x,
            y: y,
            radius: isGateway ? CONFIG.NODE_RADIUS.gateway :
                d.device_type === 'server' ? CONFIG.NODE_RADIUS.server :
                    CONFIG.NODE_RADIUS.default
        };
    });

    // Links: todos conectados al gateway
    const gateway = nodes.find(n => n.is_gateway);
    const links = gateway ? nodes
        .filter(n => !n.is_gateway)
        .map(n => ({
            source: gateway.id,
            target: n.id
        })) : [];

    // Crear grupos
    const g = svg.append('g');

    // Zoom
    const zoom = d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => g.attr('transform', event.transform));

    svg.call(zoom);

    // Centrar vista inicial
    svg.call(zoom.transform, d3.zoomIdentity.translate(width / 2, height / 2));

    // Links
    const link = g.append('g')
        .attr('class', 'links')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('class', 'link');

    // Nodes
    const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr('class', d => `node ${d.is_gateway ? 'gateway' : ''} ${d.is_online ? 'online' : ''} node-enter`)
        .style('--node-color', d => getDeviceColor(d.device_type))
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended))
        .on('mouseover', showTooltip)
        .on('mousemove', moveTooltip)
        .on('mouseout', hideTooltip)
        .on('click', showDevicePanel);

    // Node circles
    node.append('circle')
        .attr('class', 'node-circle')
        .attr('r', d => d.radius)
        .attr('fill', d => getDeviceColor(d.device_type))
        .attr('stroke', d => d3.color(getDeviceColor(d.device_type)).brighter(0.5));

    // Node icons
    node.append('text')
        .attr('class', 'node-icon')
        .text(d => getDeviceIcon(d.device_type));

    // Node labels
    node.append('text')
        .attr('class', 'node-label')
        .attr('dy', d => d.radius + 16)
        .text(d => d.hostname || d.ip.split('.').pop());

    // Force simulation - Pre-calcular posiciones antes de renderizar
    state.simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(100).strength(0.1))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('collision', d3.forceCollide().radius(d => d.radius + 20).strength(1))
        .stop(); // Detener antes de asignar on('tick')

    // Pre-calcular posiciones (300 iteraciones)
    for (let i = 0; i < 300; i++) {
        state.simulation.tick();
    }

    // Ahora renderizar con posiciones ya calculadas
    link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

    node.attr('transform', d => `translate(${d.x},${d.y})`);

    // Reiniciar simulación para permitir arrastrar nodos
    state.simulation
        .on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            node.attr('transform', d => `translate(${d.x},${d.y})`);
        })
        .alpha(0.1)
        .restart();
}

// Drag functions
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

// ============================================
// Helpers
// ============================================
function getDeviceColor(type) {
    return DEVICE_CONFIG[type]?.color || DEVICE_CONFIG.unknown.color;
}

function getDeviceIcon(type) {
    return DEVICE_CONFIG[type]?.icon || DEVICE_CONFIG.unknown.icon;
}

function getDeviceLabel(type) {
    return DEVICE_CONFIG[type]?.label || DEVICE_CONFIG.unknown.label;
}

// ============================================
// Tooltip
// ============================================
function showTooltip(event, d) {
    const config = DEVICE_CONFIG[d.device_type] || DEVICE_CONFIG.unknown;

    elements.tooltip.innerHTML = `
        <div class="tooltip-header">
            <span class="tooltip-icon">${config.icon}</span>
            <div>
                <div class="tooltip-hostname">${d.hostname || 'Sin nombre'}</div>
                <div class="tooltip-ip">${d.ip}</div>
            </div>
        </div>
        <div class="tooltip-details">
            <div class="tooltip-row">
                <span class="tooltip-label">Tipo</span>
                <span>${config.label}</span>
            </div>
            <div class="tooltip-row">
                <span class="tooltip-label">MAC</span>
                <span>${d.mac || 'N/A'}</span>
            </div>
            ${d.vendor ? `
            <div class="tooltip-row">
                <span class="tooltip-label">Vendor</span>
                <span>${d.vendor}</span>
            </div>
            ` : ''}
        </div>
    `;

    elements.tooltip.classList.add('visible');
    moveTooltip(event);
}

function moveTooltip(event) {
    const tooltip = elements.tooltip;
    const x = event.pageX + 15;
    const y = event.pageY + 15;

    // Evitar que salga de la pantalla
    const maxX = window.innerWidth - tooltip.offsetWidth - 20;
    const maxY = window.innerHeight - tooltip.offsetHeight - 20;

    tooltip.style.left = `${Math.min(x, maxX)}px`;
    tooltip.style.top = `${Math.min(y, maxY)}px`;
}

function hideTooltip() {
    elements.tooltip.classList.remove('visible');
}

// ============================================
// Device Panel
// ============================================
function showDevicePanel(event, d) {
    const config = DEVICE_CONFIG[d.device_type] || DEVICE_CONFIG.unknown;

    elements.panelTitle.innerHTML = `${config.icon} ${d.hostname || d.ip}`;
    elements.panelContent.innerHTML = `
        <div class="panel-section">
            <div class="panel-section-title">Información General</div>
            <div class="panel-info-grid">
                <div class="panel-info-item">
                    <span class="panel-info-label">IP</span>
                    <span class="panel-info-value">${d.ip}</span>
                </div>
                <div class="panel-info-item">
                    <span class="panel-info-label">MAC</span>
                    <span class="panel-info-value">${d.mac || 'N/A'}</span>
                </div>
                <div class="panel-info-item">
                    <span class="panel-info-label">Tipo</span>
                    <span class="panel-info-value">${config.label}</span>
                </div>
                ${d.vendor ? `
                <div class="panel-info-item">
                    <span class="panel-info-label">Vendor</span>
                    <span class="panel-info-value">${d.vendor}</span>
                </div>
                ` : ''}
                <div class="panel-info-item">
                    <span class="panel-info-label">Estado</span>
                    <span class="panel-info-value" style="color: ${d.is_online ? '#22c55e' : '#ef4444'}">
                        ${d.is_online ? '🟢 Online' : '🔴 Offline'}
                    </span>
                </div>
                ${d.is_gateway ? `
                <div class="panel-info-item">
                    <span class="panel-info-label">Rol</span>
                    <span class="panel-info-value" style="color: #22c55e">🌐 Gateway</span>
                </div>
                ` : ''}
            </div>
        </div>
        
        <div class="panel-section">
            <div class="panel-section-title">Personalizar</div>
            <div class="edit-form">
                <div class="form-group">
                    <label>Nombre personalizado</label>
                    <input type="text" id="editName" value="${d.custom_name || ''}" placeholder="${d.hostname || 'Sin nombre'}">
                </div>
                <div class="form-group">
                    <label>Tipo</label>
                    <select id="editType">
                        ${Object.keys(DEVICE_CONFIG).map(type =>
        `<option value="${type}" ${d.device_type === type ? 'selected' : ''}>${DEVICE_CONFIG[type].icon} ${DEVICE_CONFIG[type].label}</option>`
    ).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Notas</label>
                    <textarea id="editNotes" rows="2" placeholder="Agregar notas...">${d.notes || ''}</textarea>
                </div>
                <div class="form-group" style="flex-direction: row; gap: 16px;">
                    <label style="display: flex; align-items: center; gap: 8px;">
                        <input type="checkbox" id="editFavorite" ${d.is_favorite ? 'checked' : ''}>
                        ⭐ Favorito
                    </label>
                </div>
                <button class="btn btn-primary" onclick="saveDeviceChanges('${d.ip}')" style="width: 100%; margin-top: 8px;">
                    💾 Guardar Cambios
                </button>
            </div>
        </div>
        
        <div class="panel-section">
            <div class="panel-section-title">Escaneo Avanzado</div>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <select id="scanTypeSelect" class="scan-select">
                    <option value="quick">⚡ Rápido (~30s)</option>
                    <option value="standard" selected>📊 Estándar (~2min)</option>
                    <option value="web">🌐 Web - HTTP/SSL</option>
                    <option value="iot">🔌 IoT - MQTT/UPnP</option>
                    <option value="smarthome">💡 Smart Home</option>
                    <option value="vuln">🔓 Vulnerabilidades</option>
                    <option value="aggressive">⚠️ Agresivo</option>
                    <option value="stealth">🥷 Sigiloso</option>
                    <option value="full">📋 Completo (~10min)</option>
                </select>
                <button class="btn btn-primary" onclick="deepScan('${d.ip}')" style="width: 100%;">
                    🔍 Ejecutar Escaneo
                </button>
            </div>
        </div>
        
        <div class="panel-section">
            <div class="panel-section-title">Acciones Rápidas</div>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <button class="btn btn-secondary" onclick="wakeDevice('${d.ip}')" style="width: 100%;" ${!d.mac ? 'disabled title="Sin MAC"' : ''}>
                    ⚡ Wake-on-LAN
                </button>
                <button class="btn btn-secondary" onclick="window.open('http://${d.ip}', '_blank')" style="width: 100%;">
                    🌐 Abrir en navegador
                </button>
                <button class="btn btn-secondary" onclick="viewDeviceHistory('${d.ip}')" style="width: 100%;">
                    📊 Ver Historial
                </button>
            </div>
        </div>
        
        <div class="panel-section" id="deepScanResults"></div>
    `;

    elements.devicePanel.classList.add('open');
}

function closeDevicePanel() {
    elements.devicePanel.classList.remove('open');
}

// Guardar cambios del dispositivo
async function saveDeviceChanges(ip) {
    const updates = {
        custom_name: document.getElementById('editName').value || null,
        custom_type: document.getElementById('editType').value,
        notes: document.getElementById('editNotes').value || null,
        is_favorite: document.getElementById('editFavorite').checked
    };

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/devices/${ip}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });

        if (response.ok) {
            // Actualizar dispositivo local
            const device = state.devices.find(d => d.ip === ip);
            if (device) {
                Object.assign(device, updates);
            }

            // Feedback visual
            const btn = event.target;
            btn.textContent = '✅ Guardado!';
            btn.style.background = 'var(--color-success)';

            setTimeout(() => {
                btn.textContent = '💾 Guardar Cambios';
                btn.style.background = '';
            }, 2000);

            // Re-renderizar para reflejar cambios
            renderNetwork();
        } else {
            alert('Error al guardar');
        }
    } catch (error) {
        console.error('[Save] Error:', error);
        alert('Error de conexión');
    }
}

// Deep scan individual device
async function deepScan(ip) {
    const resultsDiv = document.getElementById('deepScanResults');
    const scanType = document.getElementById('scanTypeSelect')?.value || 'standard';

    const scanTypeNames = {
        quick: 'Rápido', standard: 'Estándar', full: 'Completo',
        vuln: 'Vulnerabilidades', stealth: 'Sigiloso', aggressive: 'Agresivo',
        web: 'Web', iot: 'IoT', smarthome: 'Smart Home'
    };

    resultsDiv.innerHTML = `
        <div class="panel-section-title">Escaneo ${scanTypeNames[scanType] || scanType}</div>
            <p style="color: var(--text-muted); font-size: 13px;">
                <span class="scanning-indicator"></span> Escaneando...
            </p>
    `;

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/devices/${ip}/deep-scan?scan_type=${scanType}`);
        const data = await response.json();

        if (data.error) {
            resultsDiv.innerHTML = `
                <div class="panel-section-title">Escaneo Profundo</div>
                <p style="color: var(--color-error); font-size: 13px;">Error: ${data.error}</p>
            `;
            return;
        }

        // Puertos abiertos
        const portsHtml = data.ports?.length ? `
            <div class="panel-ports-list">
                ${data.ports.map(p => `
                    <div class="port-item ${p.state === 'open' ? 'open' : ''}">
                        <span class="port-number">${p.port}/${p.protocol}</span>
                        <span class="port-service">${p.service || 'unknown'}</span>
                        ${p.product ? `<span class="port-product">${p.product} ${p.version || ''}</span>` : ''}
                    </div>
                `).join('')}
            </div>
        ` : '<p style="color: var(--text-muted); font-size: 13px;">No se detectaron puertos abiertos</p>';

        // OS Detection
        const osHtml = data.os?.length ? `
            <div class="scan-result-item">
                <span class="result-label">🖥️ Sistema Operativo</span>
                <span class="result-value">${data.os[0]?.name || 'Desconocido'}</span>
                <span class="result-accuracy">${data.os[0]?.accuracy || '?'}% certeza</span>
            </div>
        ` : '';

        // Scripts NSE (para web, iot, vuln scans)
        const scriptsHtml = data.scripts?.length || data.ports?.some(p => p.scripts?.length) ? `
            <div class="panel-section-title" style="margin-top: 12px;">📜 Scripts NSE</div>
            <div class="scripts-list">
                ${data.scripts?.map(s => `
                    <div class="script-item">
                        <span class="script-name">${s.name}</span>
                        <pre class="script-output">${s.output?.substring(0, 200) || 'Sin output'}</pre>
                    </div>
                `).join('') || ''}
                ${data.ports?.filter(p => p.scripts?.length).map(p => p.scripts.map(s => `
                    <div class="script-item">
                        <span class="script-name">${p.port}: ${s.name}</span>
                        <pre class="script-output">${s.output?.substring(0, 200) || ''}</pre>
                    </div>
                `).join('')).join('') || ''}
            </div>
        ` : '';

        // Uptime
        const uptimeHtml = data.uptime?.seconds ? `
            <div class="scan-result-item">
                <span class="result-label">⏱️ Uptime</span>
                <span class="result-value">${Math.floor(data.uptime.seconds / 86400)} días</span>
            </div>
        ` : '';

        resultsDiv.innerHTML = `
            <div class="panel-section-title">Resultados (${data.ports?.length || 0} puertos)</div>
            ${portsHtml}
            ${osHtml}
            ${uptimeHtml}
            ${scriptsHtml}
        `;

    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="panel-section-title">Escaneo</div>
            <p style="color: var(--color-error); font-size: 13px;">Error de conexión</p>
        `;
    }
}

// Wake-on-LAN
async function wakeDevice(ip) {
    try {
        const response = await fetch(`${CONFIG.API_URL}/api/devices/${ip}/wake`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            showNotification('⚡ ' + data.message, 'success');
        } else {
            showNotification('❌ ' + (data.error || 'Error al despertar'), 'error');
        }
    } catch (error) {
        showNotification('❌ Error de conexión', 'error');
    }
}

// View device history
async function viewDeviceHistory(ip) {
    const resultsDiv = document.getElementById('deepScanResults');
    resultsDiv.innerHTML = `
        <div class="panel-section-title">📊 Historial</div>
        <p style="color: var(--text-muted); font-size: 13px;">Cargando...</p>
    `;

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/devices/${ip}/history?limit=10`);
        const data = await response.json();

        if (data.history && data.history.length > 0) {
            const historyHtml = data.history.map(h => `
                <div class="history-item">
                    <span class="history-time">${new Date(h.scan_timestamp).toLocaleString()}</span>
                    <span class="history-status ${h.is_online ? 'online' : 'offline'}">${h.is_online ? '🟢' : '🔴'}</span>
                </div>
            `).join('');

            resultsDiv.innerHTML = `
                <div class="panel-section-title">📊 Historial (${data.history.length})</div>
                <div class="history-list">${historyHtml}</div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div class="panel-section-title">📊 Historial</div>
                <p style="color: var(--text-muted); font-size: 13px;">Sin datos históricos</p>
            `;
        }
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="panel-section-title">📊 Historial</div>
            <p style="color: var(--color-error); font-size: 13px;">Error al cargar</p>
        `;
    }
}

// Show notification toast
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Export devices
function exportDevices(format = 'json') {
    window.open(`${CONFIG.API_URL}/api/export?format=${format}`, '_blank');
}

// ============================================
// Event Listeners
// ============================================
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

// Resize handler
window.addEventListener('resize', () => {
    if (state.devices.length > 0) {
        renderNetwork();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeDevicePanel();
    }
    if (e.key === 'r' && !e.ctrlKey && !e.metaKey && document.activeElement.tagName !== 'INPUT') {
        triggerScan('quick');
    }
});

// Search and filter handlers
if (elements.searchInput) {
    elements.searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value.toLowerCase();
        renderNetwork();
    });
}

if (elements.filterType) {
    elements.filterType.addEventListener('change', (e) => {
        state.filterType = e.target.value;
        renderNetwork();
    });
}

// Layout mode toggle
if (elements.layoutMode) {
    elements.layoutMode.addEventListener('change', (e) => {
        state.layoutMode = e.target.value;
        renderNetwork();
    });
}

// Theme toggle
if (elements.btnTheme) {
    elements.btnTheme.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        const isLight = document.body.classList.contains('light-theme');
        elements.btnTheme.textContent = isLight ? '🌞' : '🌙';
        localStorage.setItem('theme', isLight ? 'light' : 'dark');
    });

    // Load saved theme
    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.add('light-theme');
        elements.btnTheme.textContent = '🌞';
    }
}

// Export button
if (elements.btnExport) {
    elements.btnExport.addEventListener('click', () => {
        const menu = document.createElement('div');
        menu.className = 'export-menu';
        menu.innerHTML = `
            <button onclick="exportDevices('json'); this.parentElement.remove();">📄 JSON</button>
            <button onclick="exportDevices('csv'); this.parentElement.remove();">📊 CSV</button>
        `;
        menu.style.cssText = 'position:absolute;top:50px;right:100px;background:var(--glass-bg);padding:8px;border-radius:8px;display:flex;gap:8px;z-index:1000;';
        document.body.appendChild(menu);
        setTimeout(() => menu.remove(), 5000);
    });
}

// Alerts button
if (elements.btnAlerts) {
    elements.btnAlerts.addEventListener('click', async () => {
        try {
            const response = await fetch(`${CONFIG.API_URL}/api/alerts?limit=20`);
            const data = await response.json();

            if (data.alerts && data.alerts.length > 0) {
                const alertsHtml = data.alerts.slice(0, 10).map(a => `
                    <div class="alert-item ${a.is_read ? '' : 'unread'}">
                        <span class="alert-icon">${a.alert_type === 'new_device' ? '🟢' : '🔴'}</span>
                        <span class="alert-message">${a.message}</span>
                        <span class="alert-time">${new Date(a.timestamp).toLocaleTimeString()}</span>
                    </div>
                `).join('');

                showNotification(`📋 ${data.alerts.length} alertas`, 'info');
            } else {
                showNotification('📋 Sin alertas', 'info');
            }
        } catch (error) {
            showNotification('❌ Error al cargar alertas', 'error');
        }
    });
}

// Filter devices function
function getFilteredDevices() {
    let devices = state.devices;

    // Search filter
    if (state.searchQuery) {
        devices = devices.filter(d =>
            d.ip?.toLowerCase().includes(state.searchQuery) ||
            d.hostname?.toLowerCase().includes(state.searchQuery) ||
            d.vendor?.toLowerCase().includes(state.searchQuery) ||
            d.custom_name?.toLowerCase().includes(state.searchQuery)
        );
    }

    // Type filter
    if (state.filterType && state.filterType !== 'all') {
        devices = devices.filter(d =>
            d.device_type === state.filterType || d.custom_type === state.filterType
        );
    }

    return devices;
}

// ============================================
// Initialize
// ============================================
function init() {
    console.log('🌐 Network Scanner iniciando...');
    connectWebSocket();

    // Fallback: si WebSocket falla después de 5 segundos, usar REST
    setTimeout(() => {
        if (!state.isConnected && state.devices.length === 0) {
            console.log('[Init] WebSocket no conectado, usando REST API');
            triggerScan('quick');
        }
    }, 5000);

    // Initialize terminal
    initTerminal();
}

// ============================================
// Hacker Terminal Module
// ============================================
const terminal = {
    panel: null,
    log: null,
    input: null,
    graph: null,
    graphCtx: null,
    activityData: [],
    startTime: Date.now()
};

function initTerminal() {
    terminal.panel = document.getElementById('terminalPanel');
    terminal.log = document.getElementById('terminalLog');
    terminal.input = document.getElementById('terminalInput');
    terminal.graph = document.getElementById('activityGraph');

    if (!terminal.panel) return;

    // Toggle terminal
    const toggleBtn = document.getElementById('btnToggleTerminal');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            terminal.panel.classList.toggle('minimized');
        });
    }

    // Command input
    if (terminal.input) {
        terminal.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const cmd = terminal.input.value.trim().toLowerCase();
                processCommand(cmd);
                terminal.input.value = '';
            }
        });
    }

    // Init activity graph
    if (terminal.graph) {
        terminal.graphCtx = terminal.graph.getContext('2d');
        terminal.graph.width = terminal.graph.offsetWidth;
        terminal.activityData = new Array(100).fill(0);
        drawActivityGraph();
    }

    // Start uptime timer
    setInterval(updateUptime, 1000);

    // Log initial message
    termLog('SYS', 'Terminal inicializada', 'info');
    termLog('SYS', 'Escriba "help" para ver comandos', 'info');
}

function termLog(type, message, level = 'success') {
    if (!terminal.log) return;

    const time = new Date().toLocaleTimeString('es-ES');
    const line = document.createElement('div');
    line.className = 'log-line';
    line.innerHTML = `<span class="log-time">${time}</span> <span class="log-${level}">[${type}]</span> ${message}`;

    terminal.log.appendChild(line);
    terminal.log.scrollTop = terminal.log.scrollHeight;

    // Limit log lines
    while (terminal.log.children.length > 50) {
        terminal.log.removeChild(terminal.log.firstChild);
    }

    // Add activity spike
    addActivitySpike(level === 'scan' ? 80 : level === 'warning' ? 60 : 30);
}

function processCommand(cmd) {
    termLog('CMD', `> ${cmd}`, 'info');

    switch (cmd) {
        case 'help':
            termLog('SYS', 'Comandos: scan, status, clear, devices, ping, wol [ip]', 'info');
            break;
        case 'scan':
            termLog('SCAN', 'Iniciando escaneo de red...', 'scan');
            triggerScan('quick');
            break;
        case 'clear':
            terminal.log.innerHTML = '';
            break;
        case 'status':
            termLog('SYS', `Hosts: ${state.devices.length} | Conectado: ${state.isConnected}`, 'success');
            break;
        case 'devices':
            state.devices.forEach(d => {
                termLog('DEV', `${d.ip} - ${d.hostname || 'unknown'} [${d.device_type}]`, 'info');
            });
            break;
        case 'ping':
            termLog('NET', 'Ejecutando ping a todos los hosts...', 'scan');
            fetch(`${CONFIG.API_URL}/api/latency/refresh`, { method: 'POST' })
                .then(r => r.json())
                .then(data => termLog('NET', `Ping completado: ${data.refreshed} hosts`, 'success'))
                .catch(() => termLog('NET', 'Error en ping', 'error'));
            break;
        default:
            if (cmd.startsWith('wol ')) {
                const ip = cmd.split(' ')[1];
                termLog('WOL', `Enviando Wake-on-LAN a ${ip}...`, 'scan');
                fetch(`${CONFIG.API_URL}/api/devices/${ip}/wake`, { method: 'POST' })
                    .then(r => r.json())
                    .then(data => termLog('WOL', data.message || 'Magic packet enviado', 'success'))
                    .catch(() => termLog('WOL', 'Error WoL', 'error'));
            } else if (cmd) {
                termLog('ERR', `Comando no reconocido: ${cmd}`, 'error');
            }
    }
}

function addActivitySpike(value) {
    terminal.activityData.push(value);
    if (terminal.activityData.length > 100) {
        terminal.activityData.shift();
    }
    drawActivityGraph();
}

function drawActivityGraph() {
    if (!terminal.graphCtx) return;

    const ctx = terminal.graphCtx;
    const w = terminal.graph.width;
    const h = terminal.graph.height;

    ctx.clearRect(0, 0, w, h);

    // Draw grid
    ctx.strokeStyle = 'rgba(0, 255, 0, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 5; i++) {
        ctx.beginPath();
        ctx.moveTo(0, (h / 5) * i);
        ctx.lineTo(w, (h / 5) * i);
        ctx.stroke();
    }

    // Draw activity line
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 2;
    ctx.shadowColor = '#00ff00';
    ctx.shadowBlur = 10;
    ctx.beginPath();

    const step = w / (terminal.activityData.length - 1);
    terminal.activityData.forEach((val, i) => {
        const x = i * step;
        const y = h - (val / 100 * h);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Decay values
    terminal.activityData = terminal.activityData.map(v => Math.max(0, v - 1));
}

function updateUptime() {
    const uptime = document.getElementById('termUptime');
    if (!uptime) return;

    const elapsed = Math.floor((Date.now() - terminal.startTime) / 1000);
    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    uptime.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
}

function updateTerminalStats() {
    const hosts = document.getElementById('termDeviceCount');
    const ports = document.getElementById('termPortsOpen');
    const alerts = document.getElementById('termAlerts');

    if (hosts) hosts.textContent = state.devices.length;
    if (ports) {
        const totalPorts = state.devices.reduce((sum, d) => sum + (d.ports?.length || 0), 0);
        ports.textContent = totalPorts;
    }
    if (alerts) alerts.textContent = state.unreadAlerts;
}

// Hook into scan updates
const originalUpdateDevices = typeof updateDevices === 'function' ? updateDevices : null;
if (originalUpdateDevices) {
    window.updateDevices = function (devices) {
        originalUpdateDevices(devices);
        updateTerminalStats();
        termLog('SCAN', `Escaneo completado: ${devices.length} hosts detectados`, 'scan');
    };
}

// ============================================
// Inventory View Logic (Enhanced)
// ============================================

let inventoryData = null; // Store for filtering

window.switchView = function (viewName) {
    // Update tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.view === viewName);
    });

    // Update containers
    const graphView = document.getElementById('graphView');
    const inventoryView = document.getElementById('inventoryView');

    if (viewName === 'inventory') {
        if (graphView) graphView.style.display = 'none';
        if (inventoryView) {
            inventoryView.style.display = 'block';
            fetchInventory();
        }
    } else {
        if (graphView) graphView.style.display = 'flex';
        if (inventoryView) inventoryView.style.display = 'none';
        if (state.simulation) state.simulation.restart();
    }
}

async function fetchInventory() {
    const grid = document.getElementById('inventoryGrid');
    if (!grid) return;

    grid.innerHTML = `
        <div class="scanning-animation" style="margin: 50px auto;">
            <div class="scanning-ring"></div>
            <p class="scanning-text">Cargando inventario...</p>
        </div>
    `;

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/inventory`);
        if (!response.ok) throw new Error('Error cargando inventario');

        inventoryData = await response.json();
        updateInventoryStats(inventoryData);
        renderInventory(inventoryData.items);
    } catch (error) {
        console.error("Inventory error:", error);
        grid.innerHTML = `<div style="text-align:center; color: var(--color-error); padding: 50px;">Error: ${error.message}</div>`;
    }
}

function updateInventoryStats(data) {
    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    setVal('invTotal', data.total_hosts || 0);
    setVal('invOnline', data.online_hosts || 0);
    setVal('invDoc', data.documented_hosts || 0);
    setVal('invRogue', data.rogue_hosts || 0);
}

function getFilteredItems() {
    if (!inventoryData || !inventoryData.items) return [];

    const searchEl = document.getElementById('inventorySearch');
    const filterEl = document.getElementById('inventoryFilter');
    const searchTerm = (searchEl?.value || '').toLowerCase();
    const filterType = filterEl?.value || 'all';

    return inventoryData.items.filter(item => {
        // Search filter
        const searchMatch = !searchTerm ||
            (item.hostname && item.hostname.toLowerCase().includes(searchTerm)) ||
            (item.ip && item.ip.includes(searchTerm)) ||
            (item.description && item.description.toLowerCase().includes(searchTerm)) ||
            (item.vendor && item.vendor.toLowerCase().includes(searchTerm));

        if (!searchMatch) return false;

        // Type filter
        switch (filterType) {
            case 'critical': return item.is_critical;
            case 'online': return item.is_online;
            case 'offline': return !item.is_online;
            case 'documented': return item.is_documented;
            case 'rogue': return item.is_rogue;
            default: return true;
        }
    });
}

function renderInventory(items) {
    const grid = document.getElementById('inventoryGrid');
    if (!grid) return;
    grid.innerHTML = '';

    const filteredItems = items || getFilteredItems();

    if (filteredItems.length === 0) {
        grid.innerHTML = '<div style="text-align:center; padding: 50px; color: var(--text-muted);">No hay dispositivos que coincidan</div>';
        return;
    }

    // Sort: Critical first, then documented, then by IP
    filteredItems.sort((a, b) => {
        if (a.is_critical !== b.is_critical) return b.is_critical - a.is_critical;
        if (a.is_documented !== b.is_documented) return b.is_documented - a.is_documented;
        if (a.is_online !== b.is_online) return b.is_online - a.is_online;
        return 0;
    });

    filteredItems.forEach(item => {
        const statusClass = item.is_online ? 'online' : 'offline';
        let typeKey = item.type ? item.type.toLowerCase() : 'unknown';
        if (typeKey === 'infrastructure') typeKey = 'server';
        const typeConfig = DEVICE_CONFIG[typeKey] || DEVICE_CONFIG.unknown;

        let badgesHtml = '';
        if (item.is_critical) badgesHtml += `<span class="tag-badge critical">CRITICAL</span>`;
        if (item.is_documented) badgesHtml += `<span class="tag-badge documented">DOC</span>`;
        if (item.is_rogue) badgesHtml += `<span class="tag-badge rogue">ROGUE</span>`;
        if (item.tags) {
            item.tags.slice(0, 3).forEach(tag => {
                const lt = tag.toLowerCase();
                if (lt !== 'critical' && lt !== 'infrastructure') {
                    badgesHtml += `<span class="tag-badge">${tag}</span>`;
                }
            });
        }

        const card = document.createElement('div');
        card.className = 'inventory-card';
        card.dataset.ip = item.ip;
        card.innerHTML = `
            <div class="card-header">
                <div class="card-icon" style="color: ${typeConfig.color}">${typeConfig.icon}</div>
                <div class="card-status ${statusClass}" title="${item.is_online ? 'Online' : 'Offline'}"></div>
            </div>
            <div class="card-body">
                <div class="card-title" title="${item.hostname}">${item.hostname}</div>
                <div class="card-subtitle">${item.ip}</div>
                <div class="card-subtitle" style="font-size: 11px;">${item.mac || '-'}</div>
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
                    ${item.description || item.vendor || 'Sin descripción'}
                </div>
                <div class="card-tags">${badgesHtml}</div>
            </div>
        `;

        // Click handler for details panel
        card.addEventListener('click', () => showInventoryDetails(item));
        grid.appendChild(card);
    });
}

function showInventoryDetails(item) {
    const panel = document.getElementById('devicePanel');
    const title = document.getElementById('panelTitle');
    const content = document.getElementById('panelContent');

    if (!panel || !content) return;

    title.textContent = item.hostname || item.ip;

    // Build specs HTML
    let specsHtml = '';
    if (item.specs && Object.keys(item.specs).length > 0) {
        specsHtml = Object.entries(item.specs).map(([k, v]) =>
            `<div class="panel-info-item"><span class="panel-info-label">${k}</span><span class="panel-info-value">${v}</span></div>`
        ).join('');
    }

    content.innerHTML = `
        <div class="panel-section">
            <div class="panel-section-title">Información General</div>
            <div class="panel-info-grid">
                <div class="panel-info-item"><span class="panel-info-label">IP</span><span class="panel-info-value">${item.ip}</span></div>
                <div class="panel-info-item"><span class="panel-info-label">MAC</span><span class="panel-info-value">${item.mac || '-'}</span></div>
                <div class="panel-info-item"><span class="panel-info-label">Tipo</span><span class="panel-info-value">${item.type}</span></div>
                <div class="panel-info-item"><span class="panel-info-label">Vendor</span><span class="panel-info-value">${item.vendor || '-'}</span></div>
                <div class="panel-info-item"><span class="panel-info-label">Estado</span><span class="panel-info-value">${item.is_online ? '🟢 Online' : '🔴 Offline'}</span></div>
                <div class="panel-info-item"><span class="panel-info-label">Crítico</span><span class="panel-info-value">${item.is_critical ? '⚠️ Sí' : 'No'}</span></div>
            </div>
        </div>
        ${item.description ? `
        <div class="panel-section">
            <div class="panel-section-title">Descripción</div>
            <p style="color: var(--text-secondary); font-size: 13px;">${item.description}</p>
        </div>` : ''}
        ${specsHtml ? `
        <div class="panel-section">
            <div class="panel-section-title">Especificaciones</div>
            <div class="panel-info-grid">${specsHtml}</div>
        </div>` : ''}
        ${item.tags && item.tags.length > 0 ? `
        <div class="panel-section">
            <div class="panel-section-title">Tags</div>
            <div class="panel-ports-list">
                ${item.tags.map(t => `<span class="port-badge">${t}</span>`).join('')}
            </div>
        </div>` : ''}
        <div class="panel-section">
            <button class="btn btn-primary" onclick="deepScan('${item.ip}')" style="width: 100%;">
                🔍 Escaneo Profundo
            </button>
        </div>
    `;

    panel.classList.add('open');
}

// Event listeners for filters
document.addEventListener('DOMContentLoaded', () => {
    const searchEl = document.getElementById('inventorySearch');
    const filterEl = document.getElementById('inventoryFilter');

    if (searchEl) {
        searchEl.addEventListener('input', () => {
            if (inventoryData) renderInventory(getFilteredItems());
        });
    }

    if (filterEl) {
        filterEl.addEventListener('change', () => {
            if (inventoryData) renderInventory(getFilteredItems());
        });
    }

    // Start terminal minimized
    const terminal = document.getElementById('terminalPanel');
    if (terminal) terminal.classList.add('minimized');
});

// Start
init();
