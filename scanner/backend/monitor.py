"""
Ping Monitor module for Network Scanner
Provides continuous latency monitoring for devices
"""
import asyncio
import subprocess
import re
from typing import Dict, Optional
from datetime import datetime

# Store latency data: {ip: {"latency_ms": float, "last_check": str, "status": str}}
latency_cache: Dict[str, Dict] = {}


def ping(ip: str, timeout: int = 2) -> Optional[float]:
    """
    Ping a single IP and return latency in ms, or None if failed
    """
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), ip],
            capture_output=True,
            text=True,
            timeout=timeout + 1
        )
        
        if result.returncode == 0:
            # Extract latency from output: "time=X.XX ms"
            match = re.search(r'time=(\d+\.?\d*)\s*ms', result.stdout)
            if match:
                return float(match.group(1))
        return None
    except (subprocess.TimeoutExpired, Exception):
        return None


async def ping_async(ip: str, timeout: int = 2) -> Optional[float]:
    """Async wrapper for ping"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: ping(ip, timeout))


async def update_device_latency(ip: str) -> Dict:
    """Update latency for a single device"""
    latency = await ping_async(ip)
    
    result = {
        "ip": ip,
        "latency_ms": latency,
        "last_check": datetime.now().isoformat(),
        "status": "online" if latency is not None else "offline"
    }
    
    latency_cache[ip] = result
    return result


async def update_all_latencies(ips: list) -> Dict[str, Dict]:
    """Update latencies for multiple IPs concurrently"""
    tasks = [update_device_latency(ip) for ip in ips]
    results = await asyncio.gather(*tasks)
    return {r["ip"]: r for r in results}


def get_latency(ip: str) -> Optional[Dict]:
    """Get cached latency for an IP"""
    return latency_cache.get(ip)


def get_all_latencies() -> Dict[str, Dict]:
    """Get all cached latencies"""
    return latency_cache.copy()


def clear_cache():
    """Clear the latency cache"""
    global latency_cache
    latency_cache = {}
