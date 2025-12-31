"""
Network Scanner API - FastAPI Application
Microservicio para escaneo y visualización de red
"""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    Device, ScanResult, NetworkInfo, DeviceUpdate, 
    DeviceCustomization, InventoryItem, InventorySummary,
    TerminalRequest, TerminalResponse
)
from scanner import get_scanner, NMAP_AVAILABLE
import storage
import database
import wol
import monitor
from telegram_notifier import notifier
try:
    from ha_client import ha_client
except ImportError:
    # Dummy class if file missing or error
    class DummyHA:
        enabled = False
    ha_client = DummyHA()


START_TIME = datetime.now()


# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Cliente conectado. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"[WS] Cliente desconectado. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"[WS] Error broadcast: {e}")


manager = ConnectionManager()


async def enrich_result_with_ha(result: ScanResult):
    """Enriquece el resultado del escaneo con datos de Home Assistant"""
    if not ha_client.enabled:
        return
        
    try:
        # Refrescar estados (optimización: tal vez no en cada scan rápido si es muy frecuente, pero cada 30s está bien)
        await ha_client.get_states()
        
        count = 0
        for dev in result.devices:
            ha_info = ha_client.get_device_info(dev.ip)
            if ha_info:
                dev.ha_data = ha_info
                # Si el hostname es desconocido o IP, usar el de HA
                if not dev.hostname or dev.hostname == dev.ip:
                    dev.hostname = ha_info['name']
                count += 1
        
        # Inyección de Dispositivos Virtuales (Zigbee/Z-Wave via HA)
        # Buscar servidor HA para usar como padre
        ha_server = next((d for d in result.devices if d.hostname == 'home-assistant' or (d.ha_data and d.ha_data.get('entity_id') == 'sensor.home_assistant_uptime')), None) # Hard to detect by entity
        # Mejor usar IP conocida o nombre
        if not ha_server:
             ha_server = next((d for d in result.devices if d.ip == '192.168.100.196'), None)
             
        if ha_server:
             virtual_dicts = ha_client.get_virtual_devices(ha_server.ip)
             if virtual_dicts:
                 print(f"[HA] Inyectando {len(virtual_dicts)} dispositivos virtuales vinculados a {ha_server.ip}")
                 for v in virtual_dicts:
                     try:
                        new_dev = Device(**v)
                        result.devices.append(new_dev)
                     except Exception as ex:
                        print(f"[HA] Error creando dispositivo virtual {v.get('hostname')}: {ex}")
                 
                 result.total_devices = len(result.devices)

        if count > 0:
            print(f"[HA] {count} dispositivos enriquecidos con datos de Home Assistant")
            
    except Exception as e:
        print(f"[HA] Error enriqueciendo datos: {e}")


# Background task for periodic scanning
# Keep track of previous devices for alerts
previous_devices_ips = set()

async def periodic_scan_task():
    """Tarea en segundo plano para escaneos periódicos"""
    global previous_devices_ips
    scanner = get_scanner()
    
    while True:
        await asyncio.sleep(30)  # Cada 30 segundos
        
        print("[Periodic] Ejecutando escaneo automático...")
        try:
            result = scanner.scan(use_nmap=False)
            
            # Enriquecer con HA
            await enrich_result_with_ha(result)
            
            result_dict = result.model_dump(mode='json')
            
            # Save to history
            database.save_scan(result_dict, scan_type="periodic")
            
            # Detect new/lost devices for alerts
            current_ips = {d.ip for d in result.devices}
            
            if previous_devices_ips:  # Skip first scan
                # New devices
                new_ips = current_ips - previous_devices_ips
                for ip in new_ips:
                    device = next((d for d in result.devices if d.ip == ip), None)
                    if device:
                        alert_id = database.create_alert(
                            alert_type="new_device",
                            ip=ip,
                            mac=device.mac,
                            hostname=device.hostname,
                            message=f"Nuevo dispositivo detectado: {device.hostname or ip}"
                        )
                        await manager.broadcast({
                            "type": "device_alert",
                            "data": {"alert_type": "new_device", "ip": ip, "hostname": device.hostname}
                        })
                        
                        # Telegram Notification
                        await notifier.notify_new_device(
                            ip=ip, 
                            mac=device.mac, 
                            hostname=device.hostname, 
                            vendor=device.vendor
                        )
                
                # Lost devices
                lost_ips = previous_devices_ips - current_ips
                for ip in lost_ips:
                    # Get device info from history/cache if possible
                    # For simplcity, we just notify ID
                    database.create_alert(
                        alert_type="device_lost",
                        ip=ip,
                        message=f"Dispositivo desaparecido: {ip}"
                    )
                    await manager.broadcast({
                        "type": "device_alert",
                        "data": {"alert_type": "device_lost", "ip": ip}
                    })
                    
                    # Telegram Notification (Optional for lost?)
                    await notifier.notify_device_lost(ip=ip)
            
            previous_devices_ips = current_ips
            
            # Broadcast to WebSocket clients
            if manager.active_connections:
                await manager.broadcast({
                    "type": "scan_update",
                    "data": result_dict
                })
                
        except Exception as e:
            print(f"[Periodic] Error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🌐 Network Scanner API iniciando...")
    
    # Initialize database
    database.init_db()
    
    scanner = get_scanner()
    print(f"📡 Red detectada: {scanner.get_network_info().network}")
    
    # Start background task
    task = asyncio.create_task(periodic_scan_task())
    
    yield
    
    # Shutdown
    task.cancel()
    print("👋 Network Scanner API detenido")


# FastAPI App
app = FastAPI(
    title="Network Scanner API",
    description="API para escaneo y visualización de red local",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/ha/analyze")
async def analyze_home_assistant():
    """Analiza la instancia de Home Assistant configurada"""
    try:
        from ha_client import ha_client
        if not ha_client.enabled:
            return {"error": "Home Assistant integration disabled"}
            
        states = await ha_client.get_states()
        if not states:
            return {"error": "Failed to fetch states from HA"}
            
        report = ha_client.analyze_potential(states)
        return {"report": report, "entity_count": len(states)}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

# ============== REST Endpoints ==============

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "nmap_available": NMAP_AVAILABLE,
        "ha_enabled": ha_client.enabled
    }


@app.get("/api/network", response_model=NetworkInfo)
async def get_network_info():
    """Obtiene información de la red local"""
    scanner = get_scanner()
    return scanner.get_network_info()


@app.get("/api/scan", response_model=ScanResult)
async def scan_network(
    use_nmap: bool = Query(False, description="Usar nmap para detección detallada"),
    scan_type: str = Query("quick", description="Tipo de escaneo: quick, standard, full, etc.")
):
    """Ejecuta un escaneo de la red
    
    - Sin nmap: Escaneo rápido con arp-scan (~2-5 segundos)
    - Con nmap: Escaneo detallado con detección de OS (~30-60 segundos)
    """
    scanner = get_scanner()
    result = scanner.scan(use_nmap=use_nmap, scan_type=scan_type)
    
    # Enriquecer con HA
    await enrich_result_with_ha(result)
    
    # Broadcast to WebSocket clients
    if manager.active_connections:
        await manager.broadcast({
            "type": "scan_complete",
            "data": result.model_dump(mode='json')
        })
    
    return result


@app.get("/api/devices/{ip}/deep-scan")
async def deep_scan_device(
    ip: str,
    scan_type: str = Query("standard", description="Tipo: quick, standard, full, vuln")
):
    """Escaneo profundo de un dispositivo específico con nmap
    
    Tipos de escaneo:
    - quick: Top 100 puertos (~30s)
    - standard: Top 1000 + OS + scripts (~2min)
    - full: Todos los puertos (~5-10min)
    - vuln: Detección de vulnerabilidades (~3min)
    """
    if not NMAP_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "nmap no está disponible"}
        )
    
    scanner = get_scanner()
    result = scanner.nmap_deep_scan(ip, scan_type=scan_type)
    
    if "error" in result:
        return JSONResponse(status_code=400, content=result)
    
    return result


@app.get("/api/devices/{ip}/vuln-scan")
async def vuln_scan_device(ip: str):
    """Escaneo de vulnerabilidades con scripts NSE"""
    if not NMAP_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "nmap no está disponible"}
        )
    
    scanner = get_scanner()
    result = scanner.nmap_vuln_scan(ip)
    
    if "error" in result:
        return JSONResponse(status_code=400, content=result)
    
    return result


@app.get("/api/devices/{ip}/services")
async def scan_services(
    ip: str,
    ports: Optional[str] = Query(None, description="Puertos: 22,80,443 o 1-1000")
):
    """Escaneo detallado de servicios en puertos específicos"""
    if not NMAP_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "nmap no está disponible"}
        )
    
    scanner = get_scanner()
    result = scanner.nmap_service_scan(ip, ports=ports)
    
    if "error" in result:
        return JSONResponse(status_code=400, content=result)
    
    return result


@app.get("/api/devices/{ip}/web-scan")
async def web_scan_device(ip: str):
    """Escaneo de servicios web: HTTP headers, SSL certs, métodos permitidos"""
    if not NMAP_AVAILABLE:
        return JSONResponse(status_code=503, content={"error": "nmap no disponible"})
    
    scanner = get_scanner()
    result = scanner.nmap_deep_scan(ip, scan_type="web")
    
    if "error" in result:
        return JSONResponse(status_code=400, content=result)
    
    return result


@app.get("/api/devices/{ip}/iot-scan")
async def iot_scan_device(ip: str):
    """Escaneo especializado para dispositivos IoT: MQTT, UPnP, CoAP"""
    if not NMAP_AVAILABLE:
        return JSONResponse(status_code=503, content={"error": "nmap no disponible"})
    
    scanner = get_scanner()
    result = scanner.nmap_deep_scan(ip, scan_type="iot")
    
    if "error" in result:
        return JSONResponse(status_code=400, content=result)
    
    return result


@app.get("/api/devices/{ip}/smarthome-scan")
async def smarthome_scan_device(ip: str):
    """Escaneo para luces y dispositivos smart home: WiZ, Hue, etc."""
    if not NMAP_AVAILABLE:
        return JSONResponse(status_code=503, content={"error": "nmap no disponible"})
    
    scanner = get_scanner()
    result = scanner.nmap_deep_scan(ip, scan_type="smarthome")
    
    if "error" in result:
        return JSONResponse(status_code=400, content=result)
    
    return result


@app.get("/api/scan-types")
async def get_scan_types():
    """Lista todos los tipos de escaneo disponibles"""
    return {
        "scan_types": [
            {"id": "quick", "name": "Rápido", "description": "Top 100 puertos, detección de versiones", "duration": "~30s"},
            {"id": "standard", "name": "Estándar", "description": "Top 1000 puertos + OS + scripts", "duration": "~2min"},
            {"id": "full", "name": "Completo", "description": "Todos los 65535 puertos", "duration": "~10min"},
            {"id": "vuln", "name": "Vulnerabilidades", "description": "Scripts NSE de seguridad", "duration": "~3min"},
            {"id": "stealth", "name": "Sigiloso", "description": "Escaneo lento y discreto", "duration": "~5min"},
            {"id": "aggressive", "name": "Agresivo", "description": "Máxima información posible", "duration": "~3min"},
            {"id": "web", "name": "Web", "description": "HTTP/HTTPS, headers, SSL", "duration": "~1min"},
            {"id": "iot", "name": "IoT", "description": "MQTT, UPnP, dispositivos conectados", "duration": "~1min"},
            {"id": "smarthome", "name": "Smart Home", "description": "WiZ, Hue, luces inteligentes", "duration": "~1min"},
        ]
    }


@app.get("/api/devices")
async def get_cached_devices():
    """Obtiene los dispositivos del último escaneo con personalizaciones aplicadas"""
    scanner = get_scanner()
    result = scanner.scan(use_nmap=False)
    
    # Aplicar personalizaciones
    customizations = storage.get_all_customizations()
    enriched_devices = []
    
    for device in result.devices:
        device_dict = device.model_dump()
        if device.ip in customizations:
            device_dict = storage.merge_with_device(device_dict, customizations[device.ip])
        enriched_devices.append(device_dict)
    
    return enriched_devices


@app.get("/api/devices/custom")
async def get_customizations():
    """Obtiene todas las personalizaciones guardadas"""
    return storage.get_all_customizations()


@app.get("/api/export")
async def export_devices(
    format: str = Query("json", regex="^(json|csv)$"),
    device_type: Optional[str] = Query(None),
    group: Optional[str] = Query(None)
):
    """Exporta los dispositivos en JSON o CSV"""
    from fastapi.responses import Response
    import csv
    import io
    
    # Get devices
    scanner = get_scanner()
    result = scanner.scan(use_nmap=False)
    
    # Apply customizations
    customizations = storage.get_all_customizations()
    devices = []
    
    for device in result.devices:
        d = device.model_dump()
        custom = customizations.get(device.ip, {})
        d.update(custom)
        
        # Apply filters
        if device_type and d.get("device_type") != device_type and d.get("custom_type") != device_type:
            continue
        if group and d.get("group") != group:
            continue
        
        devices.append(d)
    
    if format == "json":
        return {
            "exported_at": datetime.now().isoformat(),
            "total": len(devices),
            "devices": devices
        }
    
    # CSV format
    output = io.StringIO()
    if devices:
        fieldnames = ["ip", "mac", "hostname", "vendor", "device_type", "custom_name", "group", "is_gateway", "is_online"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(devices)
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=network_devices.csv"}
    )


@app.put("/api/devices/{ip}")
async def update_device(ip: str, updates: DeviceUpdate):
    """Actualiza la personalización de un dispositivo"""
    updates_dict = updates.model_dump(exclude_none=True)
    
    if not updates_dict:
        return JSONResponse(status_code=400, content={"error": "No hay cambios"})
    
    result = storage.update_customization(ip, updates_dict)
    
    if not result:
        return JSONResponse(status_code=500, content={"error": "Error guardando"})
    
    # Notificar a clientes WebSocket
    if manager.active_connections:
        await manager.broadcast({
            "type": "device_updated",
            "data": {"ip": ip, "updates": updates_dict}
        })
    
    return result


@app.delete("/api/devices/{ip}/custom")
async def delete_device_customization(ip: str):
    """Elimina la personalización de un dispositivo"""
    if storage.delete_customization(ip):
        return {"message": f"Personalización de {ip} eliminada"}
    return JSONResponse(status_code=404, content={"error": "No encontrado"})


# ============== Inventory Endpoints ==============

@app.get("/api/inventory", response_model=InventorySummary)
async def get_inventory():
    """
    Obtiene el inventario completo fusionando:
    1. Documentación (VM-Registry) - La verdad deseada
    2. Escaneo Real (Network Scanner) - La verdad actual
    """
    scanner = get_scanner()
    
    # 1. Obtener datos del registro (Verdad deseada)
    # Forzamos re-parsing para tener datos frescos
    registry_hosts = scanner.registry.parse_all()
    
    # 2. Obtener estado actual (Verdad actual)
    # Usamos el último escaneo o hacemos uno rápido si no hay
    scan_result = database.get_latest_scan()
    if not scan_result:
        # Si no hay histórico, usamos el estado actual del scanner (cache o nuevo)
        scan = scanner.scan(use_nmap=False)
        current_devices = {d.ip: d for d in scan.devices}
    else:
        # Convert dict to object-like access if needed, or simple dict lookup
        # database.get_latest_scan returns dict
        current_devices = {d['ip']: d for d in scan_result.get('devices', [])}

    inventory_items = []
    processed_ips = set()

    # A. Procesar hosts documentados
    for ip, host in registry_hosts.items():
        processed_ips.add(ip)
        
        # Check if online
        device_status = current_devices.get(ip)
        is_online = device_status is not None
        
        item = InventoryItem(
            ip=ip,
            hostname=host.name,
            type=host.type,
            description=host.description,
            is_documented=True,
            is_online=is_online,
            tags=host.tags,
            specs=host.specs,
            is_critical=host.is_critical,
            is_rogue=False
        )
        
        if is_online:
            # Enriquecer con datos reales
            # device_status is a dict if from DB, or object if from scanner.scan()
            # Let's normalize access
            if isinstance(device_status, dict):
                 item.mac = device_status.get('mac')
                 item.vendor = device_status.get('vendor')
                 # Parse ISO string to datetime if needed, or keep as string/None
                 # For safety passing to Pydantic
                 # item.last_seen = ... 
            else:
                 item.mac = device_status.mac
                 item.vendor = device_status.vendor
                 item.last_seen = device_status.last_seen

        inventory_items.append(item)

    # B. Procesar Rogues (Online pero no documentados)
    for ip, device in current_devices.items():
        if ip not in processed_ips:
            # Excluir gateway y localhost para no ensuciar, si se desea
            # Pero mejor mostrarlos como 'detectados'
            
            # Normalize access again
            if isinstance(device, dict):
                 mac = device.get('mac')
                 vendor = device.get('vendor')
                 hostname = device.get('hostname')
            else:
                 mac = device.mac
                 vendor = device.vendor
                 hostname = device.hostname

            item = InventoryItem(
                ip=ip,
                hostname=hostname or "Unknown",
                type="unknown",
                description="Dispositivo no registrado detectado en red",
                is_documented=False,
                is_online=True,
                is_rogue=True,
                mac=mac,
                vendor=vendor
            )
            inventory_items.append(item)

    # Métricas
    summary = InventorySummary(
        total_hosts=len(inventory_items),
        online_hosts=sum(1 for i in inventory_items if i.is_online),
        documented_hosts=sum(1 for i in inventory_items if i.is_documented),
        rogue_hosts=sum(1 for i in inventory_items if i.is_rogue),
        critical_hosts_offline=sum(1 for i in inventory_items if i.is_critical and not i.is_online),
        items=inventory_items
    )
    
    return summary

@app.get("/api/history")
async def get_scan_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Obtiene el historial de escaneos"""
    return {
        "scans": database.get_scan_history(limit, offset),
        "limit": limit,
        "offset": offset
    }


@app.get("/api/history/latest")
async def get_latest_scan():
    """Obtiene el último escaneo completo"""
    scan = database.get_latest_scan()
    if scan:
        return scan
    return JSONResponse(status_code=404, content={"error": "No hay escaneos"})


@app.get("/api/history/{scan_id}")
async def get_scan_by_id(scan_id: int):
    """Obtiene un escaneo específico por ID"""
    scan = database.get_scan_by_id(scan_id)
    if scan:
        return scan
    return JSONResponse(status_code=404, content={"error": "Escaneo no encontrado"})


@app.get("/api/devices/{ip}/history")
async def get_device_history(ip: str, limit: int = Query(20, ge=1, le=100)):
    """Obtiene el historial de un dispositivo específico"""
    return {
        "ip": ip,
        "history": database.get_device_history(ip, limit)
    }


# ============== Alerts Endpoints ==============

@app.get("/api/alerts")
async def get_alerts(
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False)
):
    """Obtiene las alertas del sistema"""
    return {
        "alerts": database.get_alerts(limit, unread_only),
        "unread_count": len(database.get_alerts(100, unread_only=True))
    }


@app.post("/api/alerts/read")
async def mark_alerts_read(alert_ids: List[int] = None):
    """Marca alertas como leídas"""
    database.mark_alerts_read(alert_ids)
    return {"message": "Alertas marcadas como leídas"}


# ============== Wake-on-LAN ==============

@app.post("/api/devices/{ip}/wake")
async def wake_device(ip: str):
    """Envía un magic packet Wake-on-LAN al dispositivo"""
    # Get device MAC from storage or last scan
    customizations = storage.get_all_customizations()
    device_data = customizations.get(ip, {})
    
    # Try to get MAC from customization or recent scan
    mac = device_data.get("mac")
    
    if not mac:
        # Search in latest scan
        latest = database.get_latest_scan()
        if latest:
            for device in latest.get("devices", []):
                if device.get("ip") == ip:
                    mac = device.get("mac")
                    break
    
    if not mac:
        return JSONResponse(
            status_code=400,
            content={"error": "No se encontró MAC para esta IP. Escanea primero."}
        )
    
    result = wol.wake_device(mac)
    
    if result.get("success"):
        return result
    else:
        return JSONResponse(status_code=400, content=result)


# ============== Ping / Latency ==============

@app.get("/api/devices/{ip}/ping")
async def ping_device(ip: str):
    """Ping a single device and return latency"""
    result = await monitor.update_device_latency(ip)
    return result


@app.get("/api/latency")
async def get_all_latencies():
    """Get cached latencies for all monitored devices"""
    return {
        "latencies": monitor.get_all_latencies(),
        "count": len(monitor.get_all_latencies())
    }


@app.post("/api/latency/refresh")
async def refresh_latencies():
    """Refresh latencies for all known devices"""
    # Get IPs from last scan
    latest = database.get_latest_scan()
    if not latest:
        return JSONResponse(status_code=404, content={"error": "No hay escaneo previo"})
    
    ips = [d.get("ip") for d in latest.get("devices", []) if d.get("ip")]
    results = await monitor.update_all_latencies(ips)
    
    return {
        "refreshed": len(results),
        "latencies": results
    }


# ============== WebSocket ==============

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para actualizaciones en tiempo real
    
    Eventos enviados:
    - scan_update: Resultado de escaneo periódico
    - scan_complete: Resultado de escaneo manual
    - scan_starting: Notificación de inicio de escaneo
    """
    await manager.connect(websocket)
    
    try:
        # Enviar estado inicial
        scanner = get_scanner()
        initial_scan = scanner.scan(use_nmap=False)
        await websocket.send_json({
            "type": "initial_state",
            "data": initial_scan.model_dump(mode='json')
        })
        
        # Mantener conexión viva
        while True:
            try:
                data = await websocket.receive_json()
                
                # Procesar comandos del cliente
                if data.get("action") == "scan":
                    use_nmap = data.get("use_nmap", False)
                    scan_type = data.get("scan_type", "quick")
                    await websocket.send_json({"type": "scan_starting"})
                    
                    result = scanner.scan(use_nmap=use_nmap, scan_type=scan_type)
                    await manager.broadcast({
                        "type": "scan_complete",
                        "data": result.model_dump(mode='json')
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[WS] Error: {e}")
                
    finally:
        manager.disconnect(websocket)



# ============== Terminal & Stats Endpoints ==============

@app.post("/api/terminal/command", response_model=TerminalResponse)
async def terminal_command(request: TerminalRequest):
    """Ejecuta un comando seguro desde el terminal hacker"""
    cmd = request.command.strip().lower()
    parts = cmd.split()
    
    if not parts:
        return TerminalResponse(command=cmd, output="Error: Comando vacío")

    action = parts[0]
    
    # 1. Comando HELP
    if action == "help":
        help_text = (
            "Comandos disponibles:\n"
            "  help              - Muestra esta ayuda\n"
            "  ping <ip>         - Prueba conectividad con un host\n"
            "  scan <type>       - Inicia un escaneo (quick, standard, full)\n"
            "  ha info           - Información de Home Assistant\n"
            "  pve info          - Información de Proxmox\n"
            "  clear             - Limpia la pantalla"
        )
        return TerminalResponse(command=cmd, output=help_text, status="info")

    # 2. Comando PING
    if action == "ping":
        if len(parts) < 2:
            return TerminalResponse(command=cmd, output="Error: Falta IP", status="error")
        
        target = parts[1]
        try:
            # Comando ping seguro (solo 3 paquetes)
            process = await asyncio.create_subprocess_exec(
                "ping", "-c", "3", "-W", "2", target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode().strip() or stderr.decode().strip()
            return TerminalResponse(command=cmd, output=output)
        except Exception as e:
            return TerminalResponse(command=cmd, output=f"Error ejecutando ping: {e}", status="error")

    # 3. Comando SCAN
    if action == "scan":
        scan_type = parts[1] if len(parts) > 1 else "quick"
        # Notificar por WS que iniciamos
        await manager.broadcast({"type": "scan_starting"})
        
        # Ejecutar escaneo (esto podría bloquear si no se hace en thread, pero scanner suele ser rápido o usar nmap async)
        scanner = get_scanner()
        try:
            result = scanner.scan(use_nmap=(scan_type != "quick"), scan_type=scan_type)
            await enrich_result_with_ha(result)
            
            # Guardar y notificar
            database.save_scan(result.model_dump(mode='json'), scan_type=scan_type)
            await manager.broadcast({
                "type": "scan_complete",
                "data": result.model_dump(mode='json')
            })
            
            return TerminalResponse(command=cmd, output=f"Escaneo {scan_type} completado. {len(result.devices)} dispositivos encontrados.")
        except Exception as e:
            return TerminalResponse(command=cmd, output=f"Error en escaneo: {e}", status="error")

    # 4. Comando HA
    if action == "ha":
        if not ha_client.enabled:
            return TerminalResponse(command=cmd, output="Home Assistant no está configurado", status="error")
        
        if len(parts) > 1 and parts[1] == "info":
            config = await ha_client.get_config()
            if not config:
                 return TerminalResponse(command=cmd, output="Error obteniendo info de HA", status="error")
            
            info = f"Conectado a: {ha_client.base_url}\nVersión: {config.get('version')}\nUbicación: {config.get('location_name')}"
            return TerminalResponse(command=cmd, output=info)
            
        return TerminalResponse(command=cmd, output="Uso: ha info")

    return TerminalResponse(command=cmd, output=f"Error: Comando '{action}' no reconocido", status="error")


@app.get("/api/terminal/stats")
async def get_terminal_stats():
    """Obtiene estadísticas reales para el terminal"""
    # 1. Conteo de hosts online (del último escaneo)
    latest = database.get_latest_scan()
    online_count = 0
    total_ports = 0
    
    if latest:
        devices = latest.get("devices", [])
        online_count = sum(1 for d in devices if d.get("is_online", True))
        for d in devices:
            total_ports += len(d.get("ports", []))
            
    # 2. Alertas no leídas
    unread_alerts = database.get_alerts(unread_only=True)
    
    # 3. Uptime
    uptime_delta = datetime.now() - START_TIME
    hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours:02}:{minutes:02}:{seconds:02}"
    
    # 4. Historial para el canvas (últimos 10 escaneos)
    history = database.get_scan_history(limit=12)
    activity_data = [h.get("total_devices", 0) for h in reversed(history)]
    
    return {
        "hosts": online_count,
        "ports": total_ports,
        "alerts": len(unread_alerts),
        "uptime": uptime_str,
        "activity": activity_data
    }


# ============== Entry Point ==============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
