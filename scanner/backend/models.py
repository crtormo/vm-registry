"""
Modelos Pydantic para Network Scanner
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DeviceType(str, Enum):
    ROUTER = "router"
    SERVER = "server"
    PC = "pc"
    MOBILE = "mobile"
    IOT = "iot"
    LIGHTING = "lighting"  # Luces inteligentes (WiZ, Philips Hue, etc.)
    PRINTER = "printer"
    NAS = "nas"
    VM = "vm"
    CONTAINER = "container"
    UNKNOWN = "unknown"


class Device(BaseModel):
    """Representa un dispositivo en la red"""
    ip: str
    mac: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    device_type: DeviceType = DeviceType.UNKNOWN
    is_gateway: bool = False
    is_online: bool = True
    last_seen: datetime = datetime.now()
    
    # Campos de personalización (merge con DeviceCustomization)
    custom_name: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: bool = False
    is_hidden: bool = False
    tags: List[str] = []
    
    # Integración con VM-Registry
    registry_name: Optional[str] = None
    is_rogue: bool = False  # True si no está en el registro y no es infraestructura conocida

    # Posición para visualización
    x: Optional[float] = None
    y: Optional[float] = None


class DeviceCustomization(BaseModel):
    """Personalización de un dispositivo por el usuario"""
    ip: str
    custom_name: Optional[str] = None
    custom_type: Optional[DeviceType] = None
    notes: Optional[str] = None
    is_favorite: bool = False
    is_hidden: bool = False
    tags: List[str] = []
    updated_at: datetime = datetime.now()


class DeviceUpdate(BaseModel):
    """Modelo para actualizar un dispositivo"""
    custom_name: Optional[str] = None
    custom_type: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_hidden: Optional[bool] = None
    tags: Optional[List[str]] = None
    group: Optional[str] = None  # Grupo para organización (ej: "Sala", "Oficina")


class ScanResult(BaseModel):
    """Resultado de un escaneo de red"""
    timestamp: datetime
    network: str
    gateway: str
    total_devices: int
    devices: List[Device]
    scan_duration_ms: int


class InventoryItem(BaseModel):
    """Ítem de inventario unificado (Registro + Estado en vivo)"""
    ip: str
    hostname: str
    type: str  # Del registro o detectado
    description: Optional[str] = None
    is_online: bool = False
    is_documented: bool = False  # True si está en vm-registry
    is_rogue: bool = False       # True si está en red pero no en registro
    
    # Metadata del registro
    tags: List[str] = []
    specs: Dict[str, Any] = {}
    is_critical: bool = False
    
    # Metadata del escaneo (si online)
    mac: Optional[str] = None
    vendor: Optional[str] = None
    last_seen: Optional[datetime] = None


class InventorySummary(BaseModel):
    total_hosts: int
    online_hosts: int
    documented_hosts: int
    rogue_hosts: int
    critical_hosts_offline: int
    items: List[InventoryItem]


class NetworkInfo(BaseModel):
    """Información de la red local"""
    interface: str
    ip: str
    netmask: str
    network: str
    gateway: str
    broadcast: str

