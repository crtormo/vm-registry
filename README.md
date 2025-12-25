# 🖥️ VM Registry

Registro centralizado de configuración de máquinas virtuales y servidores del homelab.

## 📁 Estructura

```
vm-registry/
├── README.md                 # Este archivo
├── machines/                 # Configuraciones de cada máquina
│   ├── proxmox-host.md      # Servidor Proxmox base
│   ├── docker-vm.md         # VM principal de Docker
│   └── ...                  # Otras VMs
├── templates/               # Plantillas para nuevas máquinas
│   └── vm-template.md       # Plantilla base
└── .history/                # Historial de cambios importantes
```

## 🏷️ Inventario de Máquinas

### 🖥️ Hypervisor

| ID | Nombre | Tipo | IP | Estado | Descripción |
|----|--------|------|-----|--------|-------------|
| - | pve | Bare-metal | 192.168.100.159 | 🟢 Activo | Proxmox VE 9.1.2 - i7-9700K, 32GB RAM |

### 💻 Máquinas Virtuales

| VMID | Nombre | IP | RAM | CPU | Estado | Descripción |
|------|--------|-----|-----|-----|--------|-------------|
| 111 | home-assistant | DHCP | 4 GB | 2 cores | 🟢 Running | Domótica |
| 115 | Docker | DHCP | 16 GB | 6 cores | 🟢 Running | **VM Principal** - Antigravity, servicios |
| 200 | gemini-test | DHCP | 16 GB | 4 cores | 🟢 Running | Testing/Desarrollo |

### 📦 Contenedores LXC

| CTID | Nombre | RAM | CPU | Estado | Descripción |
|------|--------|-----|-----|--------|-------------|
| 100 | jellyfin | 2 GB | 2 | 🔴 Stopped | Media server (deshabilitado) |
| 101 | proxmox-backup-server | 2 GB | 2 | 🟢 Running | PBS interno |
| 102 | patchmon | 2 GB | 2 | 🟢 Running | Monitoreo de parches |
| 103 | adguard | 512 MB | 1 | 🟢 Running | DNS/Ad blocker |
| 105 | jellyseerr | 4 GB | 4 | 🟢 Running | Solicitudes de media |
| 106 | npmplus | 512 MB | 1 | 🟢 Running | Nginx Proxy Manager+ |

## 📊 Resumen de Infraestructura

```
┌─────────────────────────────────────────────────────────────┐
│                    PROXMOX VE (pve)                         │
│              192.168.100.159 | i7-9700K | 32GB              │
├─────────────────────────────────────────────────────────────┤
│  VMs                          │  LXC Containers             │
│  ├── 111: home-assistant      │  ├── 101: pbs               │
│  ├── 115: Docker ⭐            │  ├── 102: patchmon          │
│  └── 200: gemini-test         │  ├── 103: adguard           │
│                               │  ├── 105: jellyseerr        │
│                               │  └── 106: npmplus           │
├─────────────────────────────────────────────────────────────┤
│  Storage                                                    │
│  ├── local-zfs (NVMe): 357GB - VMs SSD                     │
│  ├── Disco-HD (HDD): 916GB - VMs/Datos                     │
│  ├── NAS-synology (NFS): 12.6TB - Media/Backups            │
│  └── PBS-NAS: 328GB - Proxmox Backups                      │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Cómo usar

1. **Nueva VM**: Copia `templates/vm-template.md` a `machines/nombre-vm.md`
2. **Actualizar**: Edita el archivo correspondiente en `machines/`
3. **Historial**: Documenta cambios significativos en `.history/`

## 🔄 Última actualización

- **Fecha**: 2025-12-25
- **Por**: Antigravity AI Assistant
- **Cambios**: Documentación completa del servidor Proxmox y VM Docker
