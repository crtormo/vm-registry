# 🕵️ Scanner Backend

Este es el servicio backend del Scanner de Red para VM Registry. Está escrito en Python y se encarga de descubrir dispositivos, interactuar con Proxmox y Home Assistant, y mantener actualizado el inventario.

## 🚀 Funcionalidades

- **Escaneo de Red**: Utiliza `nmap` y `arp-scan` para descubrir dispositivos en la red local.
- **Integración con Proxmox**: Conecta con la API de Proxmox para obtener información sobre VMs y contenedores LXC.
- **Integración con Home Assistant**: Sincroniza estados de dispositivos y entidades.
- **Detección de Servicios**: Identifica puertos abiertos y servicios comunes (HTTP, SSH, etc.).
- **Actualización de Registro**: Actualiza los archivos Markdown del registro principal con la información encontrada.
- **WebSockets**: Proporciona actualizaciones en tiempo real al frontend.

## 🛠️ Stack Tecnológico

- **Lenguaje**: Python 3.11+
- **Framework Web**: FastAPI / WebSockets
- **Librerías Clave**:
    - `scapy`: Para manipulación de paquetes de red.
    - `requests`: Para llamadas API REST.
    - `python-nmap`: Wrapper para Nmap.
    - `paramiko`: Para conexiones SSH (si aplica).

## ⚙️ Configuración

Las variables de entorno se configuran en el `docker-compose.yml` raíz:

- `PROXMOX_HOST`, `PROXMOX_USER`, `PROXMOX_TOKEN_ID`, `PROXMOX_TOKEN_SECRET`: Credenciales de Proxmox.
- `HA_URL`, `HA_TOKEN`: Credenciales de Home Assistant.
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`: Para notificaciones (opcional).

## 🏃 Ejecución

Este servicio está diseñado para ejecutarse vía Docker Compose:

```bash
docker compose up -d scanner
```

## 📂 Estructura de Archivos

- `main.py`: Punto de entrada de la aplicación.
- `scanner.py`: Lógica principal de escaneo.
- `proxmox_client.py`: Cliente para la API de Proxmox.
- `ha_client.py`: Cliente para la API de Home Assistant.
- `registry_parser.py`: Utilidad para leer/escribir archivos del registro.
