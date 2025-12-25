# 🖥️ VM Registry

Registro centralizado de configuración de máquinas virtuales y servidores del homelab.

## 📁 Estructura

```
vm-registry/
├── README.md                      # Este archivo
├── ARCHITECTURE.md                # Diagramas visuales de arquitectura
├── machines/                      # Configuraciones de cada máquina
│   ├── proxmox-host.md           # Servidor Proxmox base
│   ├── docker-vm.md              # VM 115 - Principal ⭐
│   ├── home-assistant-vm.md      # VM 111 - Domótica
│   ├── gemini-test-vm.md         # VM 200 - Testing
│   └── lxc/                      # Contenedores LXC
│       ├── pbs-lxc.md            # LXC 101 - Backup Server
│       ├── patchmon-lxc.md       # LXC 102 - Monitoreo
│       ├── adguard-lxc.md        # LXC 103 - DNS/Ad Block
│       ├── jellyseerr-lxc.md     # LXC 105 - Media Requests
│       ├── npmplus-lxc.md        # LXC 106 - Reverse Proxy
│       └── jellyfin-lxc.md       # LXC 100 - (Detenido)
├── templates/                     # Plantillas
│   └── vm-template.md            # Plantilla base
└── .history/                      # Historial de cambios
```

## 🏷️ Inventario Rápido

### 🖥️ Hypervisor

| Nombre | IP | CPU | RAM | Descripción |
|--------|-----|-----|-----|-------------|
| **pve** | 192.168.100.159 | i7-9700K (8c) | 32 GB | Proxmox VE 9.1.2 |

### 💻 Máquinas Virtuales

| VMID | Nombre | IP | RAM | CPU | Estado |
|------|--------|-----|-----|-----|--------|
| 111 | home-assistant | DHCP | 4 GB | 2 | 🟢 |
| **115** | **Docker** ⭐ | .100.209 | 16 GB | 6 | 🟢 |
| 200 | gemini-test | DHCP | 16 GB | 4 | 🟢 |

### 📦 Contenedores LXC

| CTID | Nombre | IP | RAM | Estado | Rol |
|------|--------|-----|-----|--------|-----|
| 100 | jellyfin | - | 2 GB | 🔴 | Media (legacy) |
| 101 | pbs | .100.232 | 2 GB | 🟢 | Backups |
| 102 | patchmon | .100.228 | 2 GB | 🟢 | Monitoreo |
| 103 | **adguard** | .100.113 | 512 MB | 🟢 | **DNS** ⚡ |
| 105 | jellyseerr | .100.226 | 4 GB | 🟢 | Solicitudes |
| 106 | **npmplus** | .100.220 | 512 MB | 🟢 | **Proxy** ⚡ |

> ⚡ = Servicio crítico

---

## 🗺️ Arquitectura Visual

Ver **[ARCHITECTURE.md](./ARCHITECTURE.md)** para diagramas completos de:
- 🌐 Mapa de red
- 🔗 Flujo de servicios
- 📊 Dependencias
- 🔄 Orden de arranque

---

## 📊 Diagrama Resumen

```
                    ┌─────────────────────────────────────┐
                    │        PROXMOX VE (pve)             │
                    │      192.168.100.159:8006           │
                    │      i7-9700K | 32GB RAM            │
                    └─────────────────┬───────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
    ┌─────▼─────┐              ┌─────▼─────┐              ┌─────▼─────┐
    │ VM 111    │              │ VM 115 ⭐ │              │ VM 200    │
    │ HA        │              │ Docker    │              │ Test      │
    │ 4GB/2CPU  │              │ 16GB/6CPU │              │ 16GB/4CPU │
    └───────────┘              └─────┬─────┘              └───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
              │ MedFlix   │   │ LifeCRM   │   │ Media     │
              │ Papers    │   │ CRM       │   │ Stack     │
              └───────────┘   └───────────┘   └───────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │                    LXC CONTAINERS                           │
    ├─────────┬─────────┬─────────┬─────────┬─────────┬───────────┤
    │ PBS     │ Patchmon│ AdGuard │ Seerr   │ NPMplus │ Jellyfin  │
    │ 101 🟢  │ 102 🟢  │ 103 🟢  │ 105 🟢  │ 106 🟢  │ 100 🔴    │
    │ Backups │ Monitor │ DNS ⚡  │ Media   │ Proxy⚡ │ (legacy)  │
    └─────────┴─────────┴─────────┴─────────┴─────────┴───────────┘
```

---

## 🔗 Accesos Rápidos

| Servicio | URL |
|----------|-----|
| Proxmox VE | https://192.168.100.159:8006 |
| PBS Server | https://192.168.100.232:8007 |
| AdGuard | http://192.168.100.113 |
| NPMplus | http://192.168.100.220:81 |
| Jellyseerr | http://192.168.100.226:5055 |
| Docker VM SSH | ssh crtormo@192.168.100.209 |

---

## 📋 Cómo usar

1. **Nueva VM**: Copia `templates/vm-template.md` a `machines/nombre-vm.md`
2. **Nuevo LXC**: Copia `templates/vm-template.md` a `machines/lxc/nombre-lxc.md`
3. **Actualizar**: Edita el archivo correspondiente
4. **Arquitectura**: Actualiza `ARCHITECTURE.md` si cambian las relaciones

---

## 🔄 Última actualización

- **Fecha**: 2025-12-25
- **Por**: Antigravity AI Assistant
- **Cambios**: Documentación completa de toda la infraestructura
