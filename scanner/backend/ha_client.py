import os
import logging
import httpx
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class HomeAssistantClient:
    def __init__(self):
        self.base_url = os.getenv("HA_URL", "http://192.168.100.196:8123")
        self.token = os.getenv("HA_TOKEN")
        self.enabled = bool(self.token)
        
        if not self.enabled:
            logger.warning("Home Assistant integration disabled. Missing HA_TOKEN.")
        else:
            logger.info(f"Home Assistant integration enabled for {self.base_url}")

    async def get_config(self) -> Dict[str, Any]:
        """Obtiene configuración básica de HA"""
        if not self.enabled: return {}
        return await self._get("/api/config")

    async def get_states(self) -> List[Dict[str, Any]]:
        """Obtiene estado de todas las entidades"""
        if not self.enabled: return []
        states = await self._get("/api/states")
        if states:
            self._index_devices(states)
        return states

    def _index_devices(self, states: List[Dict[str, Any]]):
        """Indexa dispositivos por IP"""
        self.ip_index = {}
        self.states_map = {s['entity_id']: s for s in states}
        
        for s in states:
            candidates = []
            attrs = s.get('attributes', {})
            
            # 1. IP en atributos
            if 'ip_address' in attrs: candidates.append(attrs['ip_address'])
            if 'wi_fi_ip_address' in attrs: candidates.append(attrs['wi_fi_ip_address'])
            if 'lan_ip' in attrs: candidates.append(attrs['lan_ip'])
            
            # 2. IP como estado (Mobile App sensors)
            if self._is_ip(s['state']):
                candidates.append(s['state'])
            
            for ip in candidates:
                if self._is_valid_local_ip(ip):
                    self.ip_index[ip] = s

    def _is_ip(self, text):
        if not isinstance(text, str): return False
        return text.count('.') == 3 and all(p.isdigit() for p in text.replace('.', ''))

    def _is_valid_local_ip(self, ip):
        return self._is_ip(ip) and ip.startswith('192.168.')

    def get_device_info(self, ip: str) -> Dict[str, Any]:
        """Retorna info de HA para una IP dada"""
        if not self.enabled or not hasattr(self, 'ip_index'):
            return None
            
        entity = self.ip_index.get(ip)
        if not entity: return None
        
        attrs = entity['attributes']
        info = {
            "entity_id": entity['entity_id'],
            "state": entity['state'],
            "name": attrs.get('friendly_name'),
            "attributes": {} 
        }
        
        # Extract Battery
        if 'battery_level' in attrs:
            info['battery'] = attrs['battery_level']
        else:
            # Intentar encontrar sensor de batería hermano
            # Heurística: sensor.x_ip_address -> sensor.x_battery_level
            # O sensor.x_wi_fi_ip_address -> sensor.x_battery_level
            base_id = entity['entity_id']
            replacements = ['_wi_fi_ip_address', '_ip_address', '_public_ip_address']
            for r in replacements:
                if base_id.endswith(r):
                    base_id = base_id.replace(r, '')
                    break
            
            potential_battery = f"{base_id}_battery_level"
            if hasattr(self, 'states_map') and potential_battery in self.states_map:
                bat_state = self.states_map[potential_battery]['state']
                if bat_state.isdigit():
                    info['battery'] = int(bat_state)
            
            # También intentar obtener el nombre del dispositivo "padre" si el sensor tiene nombre feo
            # Ej: "S25 Ultra Wi-Fi IP" -> "S25 Ultra"
            if info['name'] and 'IP' in info['name']:
                 info['name'] = info['name'].replace(' Wi-Fi IP address', '').replace(' IP address', '')

        # Extract Unit
        if 'unit_of_measurement' in attrs:
            info['unit'] = attrs['unit_of_measurement']
            
        return info

    def get_virtual_devices(self, parent_ip: str) -> List[Dict[str, Any]]:
        """Retorna dispositivos virtuales (sin IP) para inyectar en el scanner"""
        if not self.enabled or not hasattr(self, 'states_map'):
            return []
            
        virtuals = []
        mapped_ids = set()
        
        # Collect mapped entity_ids
        if hasattr(self, 'ip_index'):
             for s in self.ip_index.values():
                 mapped_ids.add(s['entity_id'])
                 
        target_domains = ['light', 'switch', 'climate', 'lock', 'vacuum', 'media_player', 'cover', 'fan']
        
        for entity_id, s in self.states_map.items():
            domain = entity_id.split('.')[0]
            if domain in target_domains and entity_id not in mapped_ids:
                # Es un candidato virtual
                attrs = s.get('attributes', {})
                name = attrs.get('friendly_name', entity_id)
                
                # Crear estructura compatible con Device
                pseudo_ip = f"ha:{entity_id}" 
                
                virtuals.append({
                    "ip": pseudo_ip,
                    "mac": f"virtual:{entity_id}", 
                    "hostname": name,
                    "vendor": "Home Assistant (Virtual)",
                    "device_type": "iot", 
                    "parent": parent_ip,
                    "is_virtual": True,
                    "ha_data": {
                        "entity_id": entity_id,
                        "state": s['state'],
                        "attributes": attrs
                    }
                })
        return virtuals

    async def _get(self, endpoint: str) -> Any:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error requesting HA {endpoint}: {e}")
            return None

    def analyze_potential(self, states: List[Dict[str, Any]]) -> str:
        """Genera un reporte textual del potencial encontrado"""
        if not states:
            return "No se pudieron obtener datos de Home Assistant."

        domains = {}
        for state in states:
            entity_id = state['entity_id']
            domain = entity_id.split('.')[0]
            domains[domain] = domains.get(domain, 0) + 1
        
        report = ["📊 **Análisis de Potencial Home Assistant**\n"]
        report.append(f"Total entidades detectadas: {len(states)}\n")
        
        # Resumen por dominio
        report.append("### 🔌 Dominios Principales")
        for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
            icon = self._get_domain_icon(domain)
            report.append(f"- {icon} **{domain}**: {count} dispositivos")

        # Highlights específicos
        lights = [s for s in states if s['entity_id'].startswith('light.')]
        sensors = [s for s in states if s['entity_id'].startswith('sensor.')]
        cameras = [s for s in states if s['entity_id'].startswith('camera.')]
        
        report.append("\n### 💡 Oportunidades")
        if lights:
            report.append(f"- Tienes **{len(lights)} luces**. ¿Has configurado escenas 'Cine' o 'Buenas noches'?")
        if len(sensors) > 10:
            report.append(f"- Gran red de sensores (**{len(sensors)}**). Podrías crear dashboards de métricas avanzadas con Grafana.")
        if cameras:
            report.append(f"- **{len(cameras)} cámaras** detectadas. ¿Integración con detección de personas (Frigate)?")
            
        return "\n".join(report)

    def _get_domain_icon(self, domain):
        icons = {
            "light": "💡", "switch": "🔌", "sensor": "🌡️", 
            "binary_sensor": "👁️", "camera": "📷", "media_player": "🎵",
            "zone": "📍", "person": "👤", "automation": "🤖",
            "script": "📜", "scene": "🎬", "weather": "weathermap",
            "sun": "☀️", "update": "🔄"
        }
        return icons.get(domain, "📦")

ha_client = HomeAssistantClient()
