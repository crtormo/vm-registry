"""
Network Scanner usando arp-scan y nmap
"""
import subprocess
import re
import time
import socket
import netifaces
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from models import Device, DeviceType, ScanResult, NetworkInfo
from registry_parser import RegistryParser

try:
    import nmap
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False
    print("[Scanner] python-nmap no disponible, usando solo arp-scan")


# Mapeo de vendors conocidos a tipos de dispositivo
VENDOR_TYPE_MAP = {
    # Routers/Networking
    "tp-link": DeviceType.ROUTER,
    "cisco": DeviceType.ROUTER,
    "netgear": DeviceType.ROUTER,
    "ubiquiti": DeviceType.ROUTER,
    "mikrotik": DeviceType.ROUTER,
    
    # Servidores/VMs
    "proxmox": DeviceType.SERVER,
    "vmware": DeviceType.VM,
    "qemu": DeviceType.VM,
    
    # NAS
    "synology": DeviceType.NAS,
    "qnap": DeviceType.NAS,
    "western digital": DeviceType.NAS,
    
    # Móviles
    "apple": DeviceType.MOBILE,
    "samsung": DeviceType.MOBILE,
    "xiaomi": DeviceType.MOBILE,
    "huawei": DeviceType.MOBILE,
    "google": DeviceType.MOBILE,
    
    # IoT
    "espressif": DeviceType.IOT,
    "raspberry": DeviceType.IOT,
    "arduino": DeviceType.IOT,
    "tuya": DeviceType.IOT,
    "shelly": DeviceType.IOT,
    
    # Iluminación inteligente
    "signify": DeviceType.LIGHTING,  # Philips Hue, WiZ
    "wiz": DeviceType.LIGHTING,
    "philips": DeviceType.LIGHTING,
    "lifx": DeviceType.LIGHTING,
    "yeelight": DeviceType.LIGHTING,
    "nanoleaf": DeviceType.LIGHTING,
    
    # Impresoras
    "hp": DeviceType.PRINTER,
    "epson": DeviceType.PRINTER,
    "brother": DeviceType.PRINTER,
    "canon": DeviceType.PRINTER,
    
    # PCs
    "intel": DeviceType.PC,
    "realtek": DeviceType.PC,
    "dell": DeviceType.PC,
    "lenovo": DeviceType.PC,
}

# Dispositivos conocidos del homelab (de vm-registry)
KNOWN_DEVICES = {
    "192.168.100.159": ("pve", DeviceType.SERVER, "Proxmox VE"),
    "192.168.100.209": ("docker-vm", DeviceType.VM, "Docker VM Principal"),
    "192.168.100.113": ("adguard", DeviceType.CONTAINER, "AdGuard DNS"),
    "192.168.100.220": ("npmplus", DeviceType.CONTAINER, "NPMplus Proxy"),
    "192.168.100.232": ("pbs", DeviceType.CONTAINER, "PBS Backup"),
    "192.168.100.226": ("jellyseerr", DeviceType.CONTAINER, "Jellyseerr"),
    "192.168.100.228": ("patchmon", DeviceType.CONTAINER, "Patchmon"),
}


class NetworkScanner:
    """Escáner de red usando arp-scan"""
    
    def __init__(self):
        self.network_info: Optional[NetworkInfo] = None
        # Ahora el path es relativo al montaje en docker-compose (/app/vm-registry/machines)
        self.registry = RegistryParser(registry_path="/app/vm-registry/machines")
        self._detect_network()
    
    def _detect_network(self) -> None:
        """Detecta la configuración de red automáticamente"""
        try:
            # Obtener gateway por defecto
            gateways = netifaces.gateways()
            default_gateway = gateways.get('default', {}).get(netifaces.AF_INET)
            
            if not default_gateway:
                raise Exception("No se encontró gateway por defecto")
            
            gateway_ip, interface = default_gateway
            
            # Obtener info de la interfaz
            addrs = netifaces.ifaddresses(interface)
            ipv4_info = addrs.get(netifaces.AF_INET, [{}])[0]
            
            ip = ipv4_info.get('addr', '')
            netmask = ipv4_info.get('netmask', '255.255.255.0')
            broadcast = ipv4_info.get('broadcast', '')
            
            # Calcular red
            ip_parts = [int(x) for x in ip.split('.')]
            mask_parts = [int(x) for x in netmask.split('.')]
            network_parts = [ip_parts[i] & mask_parts[i] for i in range(4)]
            
            # CIDR
            cidr = sum(bin(x).count('1') for x in mask_parts)
            network = f"{'.'.join(map(str, network_parts))}/{cidr}"
            
            self.network_info = NetworkInfo(
                interface=interface,
                ip=ip,
                netmask=netmask,
                network=network,
                gateway=gateway_ip,
                broadcast=broadcast
            )
            
            print(f"[Scanner] Red detectada: {network} (gateway: {gateway_ip})")
            
        except Exception as e:
            print(f"[Scanner] Error detectando red: {e}")
            # Fallback
            self.network_info = NetworkInfo(
                interface="eth0",
                ip="192.168.100.1",
                netmask="255.255.255.0",
                network="192.168.100.0/24",
                gateway="192.168.100.1",
                broadcast="192.168.100.255"
            )
    
    def _run_arp_scan(self) -> List[Tuple[str, str, str]]:
        """Ejecuta arp-scan y parsea resultados"""
        try:
            cmd = [
                "arp-scan",
                "--localnet",
                "--interface", self.network_info.interface,
                "--retry=2",
                "--timeout=500"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            devices = []
            # Patrón: IP    MAC    Vendor
            pattern = r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:]+)\s+(.+)'
            
            for line in result.stdout.split('\n'):
                match = re.match(pattern, line.strip())
                if match:
                    ip, mac, vendor = match.groups()
                    devices.append((ip, mac.lower(), vendor.strip()))
            
            return devices
            
        except subprocess.TimeoutExpired:
            print("[Scanner] arp-scan timeout")
            return []
        except FileNotFoundError:
            print("[Scanner] arp-scan no instalado, usando fallback")
            return self._fallback_scan()
        except Exception as e:
            print(f"[Scanner] Error en arp-scan: {e}")
            return self._fallback_scan()
    
    def _fallback_scan(self) -> List[Tuple[str, str, str]]:
        """Fallback usando ARP table del sistema"""
        devices = []
        try:
            # Leer tabla ARP
            result = subprocess.run(
                ["ip", "neigh", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            for line in result.stdout.split('\n'):
                parts = line.split()
                if len(parts) >= 5 and parts[2] == 'lladdr':
                    ip = parts[0]
                    mac = parts[4].lower()
                    devices.append((ip, mac, "Unknown"))
            
        except Exception as e:
            print(f"[Scanner] Error en fallback: {e}")
        
        return devices
    
    def _identify_device_type(self, ip: str, mac: str, vendor: str) -> Tuple[DeviceType, Optional[str]]:
        """Identifica el tipo de dispositivo"""
        hostname = None
        device_type = DeviceType.UNKNOWN
        
        # Primero verificar dispositivos conocidos
        if ip in KNOWN_DEVICES:
            hostname, device_type, _ = KNOWN_DEVICES[ip]
            return device_type, hostname
        
        # Intentar resolver hostname
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            pass
        
        # Identificar por vendor
        vendor_lower = vendor.lower()
        for vendor_key, dev_type in VENDOR_TYPE_MAP.items():
            if vendor_key in vendor_lower:
                device_type = dev_type
                break
        
        return device_type, hostname
    
    def scan(self, use_nmap: bool = False, scan_type: str = "quick") -> ScanResult:
        """Ejecuta un escaneo de la red
        
        Args:
            use_nmap: Si True, usa nmap para detección detallada (más lento)
            scan_type: Tipo de escaneo (quick, standard, full, etc.)
        """
        start_time = time.time()
        
        # Primero escaneo rápido con arp-scan
        raw_devices = self._run_arp_scan()
        devices: List[Device] = []
        
        # Cargar datos del registro
        self.registry.parse_all()
        
        for ip, mac, vendor in raw_devices:
            device_type, hostname = self._identify_device_type(ip, mac, vendor)
            is_gateway = (ip == self.network_info.gateway)
            
            # Enriquecer con VM-Registry
            registry_info = self.registry.get_host_info(ip)
            registry_name = None
            is_rogue = False
            
            if registry_info:
                hostname = registry_info.name
                registry_name = registry_info.name
            else:
                # Si no está en el registro, es "unknown" o "rogue"
                # Excluimos el gateway y nosotros mismos para no generar falsos positivos excesivos al inicio
                if not is_gateway and ip != self.network_info.ip:
                    is_rogue = True
            
            device = Device(
                ip=ip,
                mac=mac,
                hostname=hostname,
                vendor=vendor if vendor != "Unknown" else None,
                device_type=device_type,
                registry_name=registry_name,
                is_rogue=is_rogue,
                is_gateway=is_gateway,
                is_online=True,
                last_seen=datetime.now()
            )
            devices.append(device)
        
        # Si se solicita nmap, enriquecer datos
        if use_nmap and NMAP_AVAILABLE:
            devices = self._enrich_with_nmap(devices, scan_type=scan_type)
        
        # Ordenar: gateway primero, luego por IP
        devices.sort(key=lambda d: (not d.is_gateway, [int(x) for x in d.ip.split('.')]))
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        return ScanResult(
            timestamp=datetime.now(),
            network=self.network_info.network,
            gateway=self.network_info.gateway,
            total_devices=len(devices),
            devices=devices,
            scan_duration_ms=elapsed_ms
        )
    
    def _enrich_with_nmap(self, devices: List[Device], scan_type: str = "quick") -> List[Device]:
        """Enriquece información de dispositivos usando nmap"""
        if not NMAP_AVAILABLE:
            return devices
        
        try:
            nm = nmap.PortScanner()
            ips = ' '.join([d.ip for d in devices])
            
            print(f"[Scanner] Ejecutando nmap en {len(devices)} dispositivos...")
            
            # Argumentos según tipo de escaneo para la red completa
            scan_args = {
                "quick": "-sn -T5 --min-rate 300",
                "standard": "-sS -sV -O --top-ports 100 -T4 --min-rate 200",
                "full": "-sS -sV -O -p- -T4 --min-rate 500",
                "web": "-sS -sV -p 80,443,8080 -T5 --min-rate 300",
                "iot": "-sS -sV -p 80,443,1883,8080 -T5 --min-rate 300",
                "smarthome": "-sS -sV -p 80,443,1883,5353,38899 -T5 --min-rate 300",
                "aggressive": "-A -T5 --min-rate 300",
                "stealth": "-sS -sV -T2 --max-retries 3",
            }
            
            args = scan_args.get(scan_type, "-sn -O --osscan-limit")
            
            print(f"[Scanner] Ejecutando nmap ({scan_type}) en {len(devices)} dispositivos...")
            
            # Ejecutar nmap con los argumentos seleccionados
            nm.scan(hosts=ips, arguments=args)
            
            for device in devices:
                if device.ip in nm.all_hosts():
                    host_info = nm[device.ip]
                    
                    # Actualizar hostname si disponible
                    if 'hostnames' in host_info and host_info['hostnames']:
                        for hn in host_info['hostnames']:
                            if hn.get('name'):
                                device.hostname = hn['name']
                                break
                    
                    # Detectar OS
                    if 'osmatch' in host_info and host_info['osmatch']:
                        os_match = host_info['osmatch'][0]
                        os_name = os_match.get('name', '').lower()
                        
                        # Mejorar detección de tipo
                        if device.device_type == DeviceType.UNKNOWN:
                            if 'linux' in os_name or 'ubuntu' in os_name or 'debian' in os_name:
                                device.device_type = DeviceType.SERVER
                            elif 'windows' in os_name:
                                device.device_type = DeviceType.PC
                            elif 'android' in os_name or 'ios' in os_name:
                                device.device_type = DeviceType.MOBILE
                            elif 'router' in os_name or 'mikrotik' in os_name:
                                device.device_type = DeviceType.ROUTER
            
            print(f"[Scanner] nmap completado")
            
        except Exception as e:
            print(f"[Scanner] Error en nmap: {e}")
        
        return devices
    
    def nmap_deep_scan(self, ip: str, scan_type: str = "standard") -> Dict[str, Any]:
        """Escaneo profundo de un dispositivo específico con nmap
        
        Args:
            ip: Dirección IP del dispositivo
            scan_type: Tipo de escaneo:
                - "quick": Puertos comunes (top 100)
                - "standard": Puertos + servicios + OS (top 1000)
                - "full": Todos los puertos + scripts NSE
                - "vuln": Escaneo de vulnerabilidades
        """
        if not NMAP_AVAILABLE:
            return {"error": "nmap no disponible"}
        
        try:
            nm = nmap.PortScanner()
            
            # Argumentos según tipo de escaneo
            # T4/T5 = timing agresivo, --min-rate = paquetes/seg mínimos
            # --max-retries = menos reintentos, --host-timeout = timeout máximo
            scan_args = {
                # Básicos - Optimizados para velocidad
                "quick": "-sS -sV --top-ports 50 -T5 --min-rate 300 --max-retries 1 --host-timeout 60s",
                "standard": "-sS -sV -O --top-ports 200 -T4 --min-rate 200 --max-retries 2 --host-timeout 120s",
                "full": "-sS -sV -O -p- -T4 --min-rate 500 --max-retries 1",
                
                # Seguridad
                "vuln": "-sS -sV --script=vuln --top-ports 100 -T4 --min-rate 200 --host-timeout 180s",
                "stealth": "-sS -sV -T2 --top-ports 100 --max-retries 3",  # Más lento pero discreto
                "aggressive": "-A -T5 --top-ports 200 --min-rate 300",     # Máxima información
                
                # Servicios específicos - Muy rápidos al tener pocos puertos
                "web": "-sS -sV -p 80,443,8080,8443,3000,5000,8000 -T5 --script=http-title,ssl-cert --min-rate 200",
                "iot": "-sS -sV -p 80,443,1883,8883,5683,8080 -T5 --script=http-title --min-rate 200",
                "smarthome": "-sS -sV -p 80,443,1883,5353,38899,38900 -T5 --script=http-title --min-rate 200",
                
                # Discovery
                "discovery": "-sn -T5 --min-rate 300",
            }
            
            args = scan_args.get(scan_type, scan_args["standard"])
            print(f"[Scanner] Deep scan {scan_type} en {ip}...")
            
            nm.scan(hosts=ip, arguments=args)
            
            if ip not in nm.all_hosts():
                return {"error": "Host no responde", "ip": ip}
            
            host = nm[ip]
            
            result = {
                "ip": ip,
                "state": host.state(),
                "scan_type": scan_type,
                "hostnames": [h['name'] for h in host.get('hostnames', []) if h.get('name')],
                "os": [],
                "ports": [],
                "scripts": [],
                "uptime": None,
                "mac": None,
                "vendor": None
            }
            
            # MAC y Vendor (si disponible)
            if 'addresses' in host:
                result["mac"] = host['addresses'].get('mac')
            if 'vendor' in host and host['vendor']:
                result["vendor"] = list(host['vendor'].values())[0] if host['vendor'] else None
            
            # Uptime
            if 'uptime' in host:
                result["uptime"] = {
                    "seconds": host['uptime'].get('seconds'),
                    "lastboot": host['uptime'].get('lastboot')
                }
            
            # OS detection con más detalle
            if 'osmatch' in host:
                for os_info in host['osmatch'][:5]:
                    os_entry = {
                        "name": os_info.get('name'),
                        "accuracy": os_info.get('accuracy'),
                        "family": None,
                        "generation": None
                    }
                    # Extraer familia del OS
                    if 'osclass' in os_info and os_info['osclass']:
                        osclass = os_info['osclass'][0]
                        os_entry["family"] = osclass.get('osfamily')
                        os_entry["generation"] = osclass.get('osgen')
                    result["os"].append(os_entry)
            
            # Puertos y servicios con más detalle
            for proto in host.all_protocols():
                for port in sorted(host[proto].keys()):
                    port_info = host[proto][port]
                    port_entry = {
                        "port": port,
                        "protocol": proto,
                        "state": port_info.get('state'),
                        "service": port_info.get('name'),
                        "product": port_info.get('product'),
                        "version": port_info.get('version'),
                        "extrainfo": port_info.get('extrainfo'),
                        "cpe": port_info.get('cpe', [])
                    }
                    
                    # Scripts ejecutados en este puerto
                    if 'script' in port_info:
                        port_entry["scripts"] = []
                        for script_name, script_output in port_info['script'].items():
                            port_entry["scripts"].append({
                                "name": script_name,
                                "output": script_output[:500]  # Limitar output
                            })
                    
                    result["ports"].append(port_entry)
            
            # Scripts globales del host
            if 'hostscript' in host:
                for script in host['hostscript']:
                    result["scripts"].append({
                        "name": script.get('id'),
                        "output": script.get('output', '')[:500]
                    })
            
            print(f"[Scanner] Deep scan completado: {len(result['ports'])} puertos encontrados")
            return result
            
        except Exception as e:
            print(f"[Scanner] Error en deep scan: {e}")
            return {"error": str(e), "ip": ip}
    
    def nmap_vuln_scan(self, ip: str) -> Dict[str, Any]:
        """Escaneo específico de vulnerabilidades con scripts NSE"""
        return self.nmap_deep_scan(ip, scan_type="vuln")
    
    def nmap_service_scan(self, ip: str, ports: str = None) -> Dict[str, Any]:
        """Escaneo detallado de servicios en puertos específicos
        
        Args:
            ip: Dirección IP
            ports: Puertos a escanear (ej: "22,80,443" o "1-1000")
        """
        if not NMAP_AVAILABLE:
            return {"error": "nmap no disponible"}
        
        try:
            nm = nmap.PortScanner()
            
            port_arg = f"-p {ports}" if ports else "--top-ports 100"
            args = f"-sV -sC {port_arg}"
            
            print(f"[Scanner] Service scan en {ip} ({ports or 'top 100'})...")
            nm.scan(hosts=ip, arguments=args)
            
            if ip not in nm.all_hosts():
                return {"error": "Host no responde"}
            
            host = nm[ip]
            services = []
            
            for proto in host.all_protocols():
                for port in sorted(host[proto].keys()):
                    p = host[proto][port]
                    if p['state'] == 'open':
                        services.append({
                            "port": port,
                            "protocol": proto,
                            "service": p.get('name', 'unknown'),
                            "product": p.get('product', ''),
                            "version": p.get('version', ''),
                            "banner": p.get('extrainfo', '')
                        })
            
            return {
                "ip": ip,
                "total_services": len(services),
                "services": services
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_network_info(self) -> NetworkInfo:
        """Retorna información de la red"""
        return self.network_info


# Singleton
scanner_instance: Optional[NetworkScanner] = None

def get_scanner() -> NetworkScanner:
    global scanner_instance
    if scanner_instance is None:
        scanner_instance = NetworkScanner()
    return scanner_instance
