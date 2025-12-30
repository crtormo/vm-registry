"""
Database module for Network Scanner - SQLite History
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import os

DATABASE_PATH = os.environ.get("DATABASE_PATH", "/app/data/network_scanner.db")


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database tables"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Scan history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                network TEXT,
                gateway TEXT,
                total_devices INTEGER,
                scan_duration_ms INTEGER,
                scan_type TEXT DEFAULT 'quick'
            )
        """)
        
        # Device snapshots for each scan
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL,
                ip TEXT NOT NULL,
                mac TEXT,
                hostname TEXT,
                vendor TEXT,
                device_type TEXT,
                is_gateway INTEGER DEFAULT 0,
                is_online INTEGER DEFAULT 1,
                ports_json TEXT,
                FOREIGN KEY (scan_id) REFERENCES scan_history(id) ON DELETE CASCADE
            )
        """)
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                ip TEXT,
                mac TEXT,
                hostname TEXT,
                message TEXT,
                is_read INTEGER DEFAULT 0
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_timestamp ON scan_history(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_device_scan ON device_snapshots(scan_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")
        
        conn.commit()
        print("[Database] Initialized successfully")


def save_scan(scan_result: Dict[str, Any], scan_type: str = "quick") -> int:
    """Save a scan result to history, returns scan_id"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Insert scan record
        cursor.execute("""
            INSERT INTO scan_history (timestamp, network, gateway, total_devices, scan_duration_ms, scan_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            scan_result.get("timestamp", datetime.now().isoformat()),
            scan_result.get("network"),
            scan_result.get("gateway"),
            scan_result.get("total_devices", 0),
            scan_result.get("scan_duration_ms", 0),
            scan_type
        ))
        
        scan_id = cursor.lastrowid
        
        # Insert device snapshots
        for device in scan_result.get("devices", []):
            cursor.execute("""
                INSERT INTO device_snapshots (scan_id, ip, mac, hostname, vendor, device_type, is_gateway, is_online, ports_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_id,
                device.get("ip"),
                device.get("mac"),
                device.get("hostname"),
                device.get("vendor"),
                device.get("device_type"),
                1 if device.get("is_gateway") else 0,
                1 if device.get("is_online", True) else 0,
                json.dumps(device.get("ports", []))
            ))
        
        conn.commit()
        return scan_id


def get_scan_history(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    """Get scan history with pagination"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM scan_history 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        return [dict(row) for row in cursor.fetchall()]


def get_scan_by_id(scan_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific scan with its devices"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get scan record
        cursor.execute("SELECT * FROM scan_history WHERE id = ?", (scan_id,))
        scan = cursor.fetchone()
        
        if not scan:
            return None
        
        result = dict(scan)
        
        # Get devices
        cursor.execute("SELECT * FROM device_snapshots WHERE scan_id = ?", (scan_id,))
        devices = []
        for row in cursor.fetchall():
            device = dict(row)
            device["ports"] = json.loads(device.pop("ports_json") or "[]")
            device["is_gateway"] = bool(device["is_gateway"])
            device["is_online"] = bool(device["is_online"])
            devices.append(device)
        
        result["devices"] = devices
        return result


def get_latest_scan() -> Optional[Dict[str, Any]]:
    """Get the most recent scan"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM scan_history ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        
        if row:
            return get_scan_by_id(row["id"])
        return None


def cleanup_old_scans(days: int = 7):
    """Remove scans older than specified days"""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scan_history WHERE timestamp < ?", (cutoff,))
        deleted = cursor.rowcount
        conn.commit()
        
        if deleted > 0:
            print(f"[Database] Cleaned up {deleted} old scans")


# Alert functions
def create_alert(alert_type: str, ip: str = None, mac: str = None, 
                 hostname: str = None, message: str = None) -> int:
    """Create a new alert"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (timestamp, alert_type, ip, mac, hostname, message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), alert_type, ip, mac, hostname, message))
        conn.commit()
        return cursor.lastrowid


def get_alerts(limit: int = 50, unread_only: bool = False) -> List[Dict[str, Any]]:
    """Get alerts with optional filter"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if unread_only:
            cursor.execute("""
                SELECT * FROM alerts WHERE is_read = 0 
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        else:
            cursor.execute("""
                SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]


def mark_alerts_read(alert_ids: List[int] = None):
    """Mark alerts as read"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if alert_ids:
            placeholders = ",".join("?" * len(alert_ids))
            cursor.execute(f"UPDATE alerts SET is_read = 1 WHERE id IN ({placeholders})", alert_ids)
        else:
            cursor.execute("UPDATE alerts SET is_read = 1")
        
        conn.commit()


def get_device_history(ip: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get historical data for a specific device"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ds.*, sh.timestamp as scan_timestamp
            FROM device_snapshots ds
            JOIN scan_history sh ON ds.scan_id = sh.id
            WHERE ds.ip = ?
            ORDER BY sh.timestamp DESC
            LIMIT ?
        """, (ip, limit))
        
        return [dict(row) for row in cursor.fetchall()]
