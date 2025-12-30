import sys
import os

# Ajustar path para importar módulos backend
sys.path.append(os.path.join(os.getcwd(), 'scanner/backend'))

from registry_parser import RegistryParser

def test_parser():
    print("Iniciando prueba de parser...")
    # Path relativo desde la raíz de vm-registry
    parser = RegistryParser(registry_path="./machines")
    hosts = parser.parse_all()
    
    print(f"Total hosts encontrados: {len(hosts)}")
    print("-" * 50)
    
    found_test = False
    for ip, host in hosts.items():
        print(f"IP: {ip} | Name: {host.name} | Type: {host.type}")
        if ip == "192.168.100.159" and host.name == "pve":
            found_test = True
            
    print("-" * 50)
    if found_test:
        print("✅ ÉXITO: Host 'pve' encontrado con IP 192.168.100.159 (Frontmatter/Legacy)")
        sys.exit(0)
    else:
        print("❌ FALLO: No se encontró el host de prueba")
        sys.exit(1)

if __name__ == "__main__":
    test_parser()
