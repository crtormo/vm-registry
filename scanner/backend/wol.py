"""
Wake-on-LAN module for Network Scanner
"""
import socket
import re
from typing import Tuple


def validate_mac(mac: str) -> Tuple[bool, str]:
    """Validate and normalize MAC address"""
    # Remove common separators
    mac_clean = re.sub(r'[:\-\.]', '', mac.upper())
    
    # Check length and hex validity
    if len(mac_clean) != 12:
        return False, "MAC debe tener 12 caracteres hex"
    
    if not re.match(r'^[0-9A-F]{12}$', mac_clean):
        return False, "MAC contiene caracteres inválidos"
    
    return True, mac_clean


def send_magic_packet(mac: str, broadcast: str = "255.255.255.255", port: int = 9) -> Tuple[bool, str]:
    """
    Send a Wake-on-LAN magic packet
    
    Args:
        mac: MAC address of target device
        broadcast: Broadcast address (default 255.255.255.255)
        port: UDP port (default 9, common WoL port)
    
    Returns:
        Tuple of (success, message)
    """
    # Validate MAC
    valid, result = validate_mac(mac)
    if not valid:
        return False, result
    
    mac_clean = result
    
    try:
        # Build magic packet: 6 bytes of 0xFF + 16 repetitions of MAC
        mac_bytes = bytes.fromhex(mac_clean)
        magic_packet = b'\xff' * 6 + mac_bytes * 16
        
        # Send via UDP broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast, port))
        sock.close()
        
        formatted_mac = ':'.join(mac_clean[i:i+2] for i in range(0, 12, 2))
        return True, f"Magic packet enviado a {formatted_mac}"
        
    except Exception as e:
        return False, f"Error enviando WoL: {str(e)}"


def wake_device(mac: str, broadcast: str = None) -> dict:
    """
    Wake a device and return result dict for API
    
    Args:
        mac: MAC address
        broadcast: Optional broadcast address
    """
    if not mac:
        return {"success": False, "error": "MAC address requerida"}
    
    broadcast_addr = broadcast or "255.255.255.255"
    success, message = send_magic_packet(mac, broadcast_addr)
    
    if success:
        return {"success": True, "message": message}
    else:
        return {"success": False, "error": message}
