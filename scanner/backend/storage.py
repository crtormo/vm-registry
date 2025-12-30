"""
Persistencia de personalizaciones de dispositivos en JSON
"""
import json
import os
from typing import Dict, Optional
from datetime import datetime
from models import DeviceCustomization, DeviceType


DATA_FILE = "/app/data/devices.json"


def _ensure_data_dir():
    """Crea el directorio de datos si no existe"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)


def _load_data() -> Dict[str, dict]:
    """Carga los datos de personalización desde el archivo JSON"""
    _ensure_data_dir()
    
    if not os.path.exists(DATA_FILE):
        return {}
    
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_data(data: Dict[str, dict]) -> None:
    """Guarda los datos de personalización en el archivo JSON"""
    _ensure_data_dir()
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def get_all_customizations() -> Dict[str, DeviceCustomization]:
    """Obtiene todas las personalizaciones"""
    data = _load_data()
    result = {}
    
    for ip, custom_data in data.items():
        try:
            result[ip] = DeviceCustomization(**custom_data)
        except Exception:
            continue
    
    return result


def get_customization(ip: str) -> Optional[DeviceCustomization]:
    """Obtiene la personalización de un dispositivo específico"""
    data = _load_data()
    
    if ip not in data:
        return None
    
    try:
        return DeviceCustomization(**data[ip])
    except Exception:
        return None


def save_customization(customization: DeviceCustomization) -> DeviceCustomization:
    """Guarda o actualiza la personalización de un dispositivo"""
    data = _load_data()
    
    customization.updated_at = datetime.now()
    data[customization.ip] = customization.model_dump(mode='json')
    
    _save_data(data)
    return customization


def update_customization(ip: str, updates: dict) -> Optional[DeviceCustomization]:
    """Actualiza parcialmente la personalización de un dispositivo"""
    data = _load_data()
    
    if ip not in data:
        # Crear nuevo
        current = {"ip": ip}
    else:
        current = data[ip]
    
    # Merge updates
    for key, value in updates.items():
        if value is not None:
            current[key] = value
    
    current["updated_at"] = datetime.now().isoformat()
    data[ip] = current
    
    _save_data(data)
    
    try:
        return DeviceCustomization(**current)
    except Exception:
        return None


def delete_customization(ip: str) -> bool:
    """Elimina la personalización de un dispositivo"""
    data = _load_data()
    
    if ip not in data:
        return False
    
    del data[ip]
    _save_data(data)
    return True


def merge_with_device(device: dict, customization: Optional[DeviceCustomization]) -> dict:
    """Merge los datos del dispositivo con su personalización"""
    if not customization:
        return device
    
    result = device.copy()
    
    if customization.custom_name:
        result["custom_name"] = customization.custom_name
    
    if customization.custom_type:
        result["device_type"] = customization.custom_type
    
    if customization.notes:
        result["notes"] = customization.notes
    
    result["is_favorite"] = customization.is_favorite
    result["is_hidden"] = customization.is_hidden
    result["tags"] = customization.tags
    
    return result
