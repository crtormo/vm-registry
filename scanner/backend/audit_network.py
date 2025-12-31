import asyncio
import json
from registry_parser import RegistryParser
from scanner import get_scanner

async def main():
    print("📋 Iniciando auditoría de red...")
    
    # 1. Parse Registry (Documented Truth)
    # Note: registry_path needs to be correct relative to container mapping
    # In container: /app/vm-registry/machines
    parser = RegistryParser(registry_path="/app/vm-registry/machines")
    documented_hosts = parser.parse_all()
    print(f"📖 Documentados: {len(documented_hosts)}")
    
    # 2. Scan Network (Ground Truth)
    scanner = get_scanner()
    print("📡 Escaneando red (esto puede tardar unos segundos)...")
    scan_result = scanner.scan(use_nmap=False)
    detected_devices = {d.ip: d for d in scan_result.devices}
    print(f"🔍 Detectados: {len(detected_devices)}")
    
    # 3. Analyze Discrepancies
    print("\n" + "="*50)
    print("🚨 DISPOSITIVOS DESCONOCIDOS (Detectados no Documentados)")
    print("="*50)
    
    unknown_count = 0
    for ip, device in detected_devices.items():
        if ip not in documented_hosts:
            # Filter out localhost/gateway if desired, but let's show all
            if device.is_gateway:
                print(f"🌐 [GATEWAY] {ip} ({device.mac}) - {device.vendor}")
            else:
                print(f"❓ [UNKNOWN] {ip} ({device.mac}) - {device.hostname or 'No Hostname'} - {device.vendor}")
                unknown_count += 1
    
    if unknown_count == 0:
        print("✅ No hay dispositivos desconocidos.")
        
    print("\n" + "="*50)
    print("👻 DISPOSITIVOS OFFLINE (Documentados no Detectados)")
    print("="*50)
    
    offline_count = 0
    for ip, host in documented_hosts.items():
        if ip not in detected_devices:
            print(f"💤 [OFFLINE] {ip} - {host.name} ({host.type})")
            offline_count += 1
            
    if offline_count == 0:
        print("✅ Todos los dispositivos documentados están online.")

    print("\n" + "="*50)
    print("✅ DISPOSITIVOS VERIFICADOS")
    print("="*50)
    for ip in documented_hosts:
        if ip in detected_devices:
            host = documented_hosts[ip]
            print(f"🆗 {ip} - {host.name}")

if __name__ == "__main__":
    asyncio.run(main())
