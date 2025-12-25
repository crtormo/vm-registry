# 🐳 Docker VM

> **Tipo**: VM  
> **Estado**: 🟢 Activo  
> **Última actualización**: 2025-12-25

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Hostname** | docker |
| **VMID Proxmox** | 115 |
| **SO** | Ubuntu 24.04.3 LTS (Noble Numbat) |
| **Versión Kernel** | 6.8.0-90-generic |
| **Propósito** | VM principal de desarrollo, servicios Docker y Antigravity |
| **Autostart** | ✅ Sí |
| **Firewall** | ✅ Habilitado |

---

## 💻 Recursos de Hardware

| Recurso | Asignado | Notas |
|---------|----------|-------|
| **CPU** | 6 cores | Intel(R) Core(TM) i7-9700K @ 3.60GHz |
| **RAM** | 10 GB | ~5.3GB en uso típico |
| **Disco** | 100 GB | LVM (`ubuntu--vg-ubuntu--lv`), 85% en uso |
| **Swap** | 4 GB | |

---

## 🌐 Configuración de Red

| Campo | Valor |
|-------|-------|
| **IP Principal** | 192.168.100.x (Por confirmar IP exacta) |
| **Gateway** | 192.168.100.1 |
| **DNS** | (Por confirmar) |
| **VLAN** | Default |
| **Interfaz** | ens18 (Típica en Proxmox) |

### Redes Docker

| Bridge | Subnet | Uso |
|--------|--------|-----|
| br-f472c51c5fe5 | - | MedFlix, LifeCRM |
| br-de1d5305d115 | - | Evolution API |
| br-1c607fad8f3e | 172.30.0.0/16 | Varios servicios |
| docker0 | 172.17.0.0/16 | Default |

---

## 🐳 Servicios Docker

### 📚 Media & Entertainment
| Contenedor | Imagen | Estado | Descripción |
|------------|--------|--------|-------------|
| audiobookshelf | ghcr.io/advplyr/audiobookshelf | 🟢 Up | Servidor de audiolibros |
| qbittorrent | lscr.io/linuxserver/qbittorrent | 🟢 Up | Cliente torrent |
| sonarr | lscr.io/linuxserver/sonarr | 🟢 Up | Gestor de series |
| radarr | lscr.io/linuxserver/radarr | 🟢 Up | Gestor de películas |
| lidarr | lscr.io/linuxserver/lidarr | 🟢 Up | Gestor de música |
| prowlarr | lscr.io/linuxserver/prowlarr | 🟢 Up | Indexador |

### 🏥 MedFlix (Proyecto Médico)
| Contenedor | Imagen | Estado | Descripción |
|------------|--------|--------|-------------|
| medflix-ui | medflix-core-ui | 🟢 Up | Frontend web |
| medflix-api | medflix-core-api | 🟢 Up | Backend API |
| medflix-bot | medflix-core-bot | 🟢 Up | Bot de Telegram |
| medflix-db | postgres:16-alpine | 🟢 Up | Base de datos |

### 👤 LifeCRM (CRM Personal)
| Contenedor | Imagen | Estado | Descripción |
|------------|--------|--------|-------------|
| lifecrm_nginx | nginx:alpine | 🟢 Up | Reverse proxy |
| lifecrm_django | lifecrm-django | 🟢 Up | Backend Django |
| lifecrm_api | lifecrm-api | 🟢 Up | API REST |
| lifecrm_celery_worker | lifecrm-celery_worker | 🟢 Up | Worker async |
| lifecrm_redis | redis:7-alpine | 🟢 Up | Cache/Queue |
| lifecrm_db | pgvector/pgvector:pg15 | 🟢 Up | PostgreSQL + pgvector |

### 📱 WhatsApp/Mensajería
| Contenedor | Imagen | Estado | Descripción |
|------------|--------|--------|-------------|
| evolution-api | atendai/evolution-api:v2.1.1 | 🟢 Up | API de WhatsApp |
| evolution-postgres | postgres:15-alpine | 🟢 Up | DB para Evolution |
| evolution-redis | redis:7-alpine | 🟢 Up | Cache para Evolution |

### 🧒 Mesada Exploradores
| Contenedor | Imagen | Estado | Descripción |
|------------|--------|--------|-------------|
| mesada-api | mesada-exploradores-api-backend | 🟢 Up | Backend del proyecto |
| mesada-mongo | mongo:6.0 | 🟢 Up | Base de datos MongoDB |

### 🎮 Gaming
| Contenedor | Imagen | Estado | Descripción |
|------------|--------|--------|-------------|
| mc-bedrock | itzg/minecraft-bedrock-server | 🟢 Up | Servidor Minecraft Bedrock |
| mc-playit | ghcr.io/playit-cloud/playit-agent | 🟢 Up | Túnel para Minecraft |

### 🔧 Infraestructura
| Contenedor | Imagen | Estado | Descripción |
|------------|--------|--------|-------------|
| n8n | n8nio/n8n | 🟢 Up | Automatización workflows |
| tailscale | tailscale/tailscale | 🟢 Up | VPN mesh |
| syncthing | syncthing/syncthing | 🟢 Up | Sincronización de archivos |
| watchtower | containrrr/watchtower | 🟢 Up | Auto-update contenedores |
| dockge-dockge-1 | louislam/dockge:1 | 🟢 Up | Gestión visual Docker |
| docker-proxy | tecnativa/docker-socket-proxy | 🟢 Up | Proxy seguro para Docker socket |

---

## 🔐 Acceso y Seguridad

| Campo | Valor |
|-------|-------|
| **Usuario principal** | crtormo |
| **Método SSH** | Key-based |
| **Firewall** | (Por verificar) |
| **Tailscale** | ✅ Habilitado |

---

## 📦 Software Instalado

### Runtime & Containers
- Docker Engine
- Docker Compose

### Herramientas de Desarrollo
- Git
- Python 3.x
- Node.js / npm

### Servicios del Sistema
- SystemD
- SSH Server

---

## 🔧 Configuraciones Especiales

### Volúmenes de Datos
Los servicios utilizan volúmenes persistentes en rutas como:
- `/data/` - Datos de aplicaciones
- Volúmenes Docker nombrados

### Networking
- Múltiples bridges Docker para aislamiento de servicios
- Tailscale para acceso remoto seguro

---

## 📝 Notas y Observaciones

- Esta es la VM principal donde corre Antigravity (yo, el asistente AI)
- Disco al 85% de capacidad - considerar limpieza o expansión
- El usuario `crtormo` es el desarrollador principal
- Todos los proyectos de desarrollo están en `/home/crtormo/antigravity/`

---

## 📜 Historial de Cambios

| Fecha | Cambio | Notas |
|-------|--------|-------|
| 2025-12-25 | Creación inicial del registro | Documentación automática por Antigravity |
