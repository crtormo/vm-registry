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
        default: 22
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
                d.device_type === 'server' ? CONFIG.NODE_RADIUS.server :
                    CONFIG.NODE_RADIUS.default
        };
    });

    const gateway = nodes.find(n => n.is_gateway);
    const links = gateway ? nodes
        .filter(n => !n.is_gateway)
        .map(n => ({ source: gateway.id, target: n.id })) : [];

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
        .attr('fill', d => getDeviceColor(d.device_type))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);

    node.append('text')
        .attr('text-anchor', 'middle')
        .attr('dy', '.3em')
        .text(d => getDeviceIcon(d.device_type))
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
    return DEVICE_CONFIG[type]?.color || DEVICE_CONFIG.unknown.color;
}

function getDeviceIcon(type) {
    return DEVICE_CONFIG[type]?.icon || DEVICE_CONFIG.unknown.icon;
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
        </div>
        <div class="panel-section">
            <h3>Acciones</h3>
             <button class="btn btn-secondary" onclick="window.open('http://${data.ip}', '_blank')">🌐 Abrir HTTP</button>
             <button class="btn btn-secondary" onclick="deepScan('${data.ip}')">🔍 Escaneo Profundo</button>
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
