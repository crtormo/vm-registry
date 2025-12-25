# 🖥️ Proxmox Host (pve)

> **Tipo**: Hypervisor (Bare-metal)  
> **Estado**: 🟢 Activo  
> **Última actualización**: 2025-12-25

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Hostname** | pve |
| **SO Base** | Debian GNU/Linux 13 (trixie) |
| **Proxmox VE** | 9.1.2 |
| **Kernel** | 6.17.2-2-pve |
| **Propósito** | Hypervisor principal del homelab |

---

## 💻 Recursos de Hardware

| Recurso | Total | Notas |
|---------|-------|-------|
| **CPU** | Intel Core i7-9700K | 8 cores @ 3.60GHz (boost hasta 4.9GHz) |
| **RAM** | 32 GB | ~25GB en uso típico |
| **Swap** | 0 GB | No configurado |

### 💾 Discos Físicos

| Dispositivo | Tamaño | Tipo | Modelo | Uso |
|-------------|--------|------|--------|-----|
| nvme0n1 | 238.5 GB | NVMe SSD | WDC PC SN520 256GB | Sistema/ZFS |
| nvme1n1 | 238.5 GB | NVMe SSD | WDC PC SN520 256GB | Sistema/ZFS |
| sda | 931.5 GB | HDD | ST1000LX015-1U7172 (SSHD) | Datos |

### 🗄️ ZFS Pool

| Pool | Tamaño | Usado | Libre | Fragmentación | Salud |
|------|--------|-------|-------|---------------|-------|
| rpool | 472 GB | 218 GB (46%) | 254 GB | 41% | 🟢 ONLINE |

---

## 🌐 Configuración de Red

| Campo | Valor |
|-------|-------|
| **IP de gestión** | 192.168.100.159 |
| **Gateway** | 192.168.100.1 |
| **Bridge principal** | vmbr0 |
| **Interfaz física** | enp69s0 |
| **WiFi** | wlp70s0 (manual/no configurado) |

### Interfaces de Red

```
auto vmbr0
iface vmbr0 inet static
    address 192.168.100.159/24
    gateway 192.168.100.1
    bridge-ports enp69s0
    bridge-stp off
    bridge-fd 0
```

---

## 💾 Storage Configurado

| Storage | Tipo | Total | Usado | Disponible | % Uso | Descripción |
|---------|------|-------|-------|------------|-------|-------------|
| local-zfs | ZFS Pool | 357 GB | 118 GB | 239 GB | 33% | Discos VM (NVMe) |
| local | Directorio | 239 GB | 380 MB | 239 GB | 0.15% | ISOs, Templates |
| Disco-HD | Directorio | 916 GB | 152 GB | 717 GB | 17% | VMs en HDD |
| NAS-synology | NFS | 12.6 TB | 4.1 TB | 8.5 TB | 33% | NAS Synology |
| PBS-NAS | PBS | 328 GB | 88 GB | 239 GB | 27% | Proxmox Backup Server |

---

## 🖥️ Máquinas Virtuales (VMs)

| VMID | Nombre | Estado | RAM | CPU | Disco | Autostart | Descripción |
|------|--------|--------|-----|-----|-------|-----------|-------------|
| 111 | home-assistant | 🟢 Running | 4 GB | 2 cores | 32 GB | ✅ | Domótica |
| 115 | Docker | 🟢 Running | 16 GB | 6 cores | 100 GB (ZFS SSD) | ✅ | **VM Principal de desarrollo** |
| 200 | gemini-test | 🟢 Running | 16 GB | 4 cores | 100 GB (HDD) | ✅ | Testing/Desarrollo |

### Detalle VMs

#### VM 111 - Home Assistant
```yaml
cores: 2
memory: 4096 MB
net0: virtio, bridge=vmbr0
boot: sata0
autostart: yes
```

#### VM 115 - Docker ⭐ (VM actual de Antigravity)
```yaml
cores: 6
memory: 16384 MB (16 GB)
net0: virtio, bridge=vmbr0, firewall=on
disk: local-zfs:vm-115-disk-0, 100GB, SSD, iothread
os: Linux (l26)
autostart: yes
```

#### VM 200 - Gemini Test
```yaml
cores: 4
memory: 16384 MB (16 GB)
net0: virtio, bridge=vmbr0, firewall=on
disk: Disco-HD:200/vm-200-disk-0.qcow2, 100GB
os: Linux (l26)
autostart: yes
```

---

## 📦 Contenedores LXC

| CTID | Nombre | Estado | RAM | CPU | Disco | SO | Descripción |
|------|--------|--------|-----|-----|-------|-----|-------------|
| 100 | jellyfin | 🔴 Stopped | 2 GB | 2 cores | 16 GB | Ubuntu | Media server (deshabilitado) |
| 101 | proxmox-backup-server | 🟢 Running | 2 GB | 2 cores | 10 GB | Debian | PBS interno |
| 102 | patchmon | 🟢 Running | 2 GB | 2 cores | 4 GB | Debian | Monitoreo de parches |
| 103 | adguard | 🟢 Running | 512 MB | 1 core | 2 GB | Debian | DNS/Ad blocker |
| 105 | jellyseerr | 🟢 Running | 4 GB | 4 cores | 8 GB | Debian | Solicitudes de media |
| 106 | npmplus | 🟢 Running | 512 MB | 1 core | 3 GB | Alpine | Nginx Proxy Manager Plus |

---

## 📊 Resumen de Recursos

### Totales del Sistema
| Recurso | Total HW | Asignado VMs | Asignado LXC | Libre |
|---------|----------|--------------|--------------|-------|
| **RAM** | 32 GB | 36 GB (overcommit) | ~9 GB | - |
| **CPU Cores** | 8 | 12 (overcommit) | 12 | - |
| **Disco** | ~1.4 TB físico | 332 GB | 43 GB | Variable |

> ⚠️ **Nota**: Hay overcommit de RAM y CPU, lo cual es normal en Proxmox siempre que no todos los recursos se usen simultáneamente al 100%.

---

## 🔐 Acceso y Seguridad

| Campo | Valor |
|-------|-------|
| **UI Web** | https://192.168.100.159:8006 |
| **Usuario** | root |
| **Método SSH** | Password |
| **PVE Firewall** | Habilitado en VMs |

---

## 📦 Software y Servicios Clave

### Componentes Proxmox
- **pve-manager**: 9.1.2
- **qemu-server**: 9.1.1
- **pve-container**: 6.0.18
- **proxmox-backup-client**: 4.1.0-1
- **ceph-fuse**: 19.2.3-pve1

### Almacenamiento
- **ZFS**: 2.3.4-pve1
- **LVM2**: 2.03.31-1+pmx1

### Red
- **ifupdown2**: 3.3.0-1+pmx11
- **FRR**: 10.4.1-1+pve1

---

## 🔌 Integraciones

| Servicio | Tipo | Descripción |
|----------|------|-------------|
| NAS Synology | NFS | Storage compartido |
| PBS-NAS | Proxmox Backup | Backups automatizados |

---

## 📝 Notas y Observaciones

- **RAM en overcommit**: 36GB asignados a VMs vs 32GB físicos - monitorear uso real
- **ZFS Pool sano**: rpool al 46% de capacidad, fragmentación 41% (normal)
- **VMs principales**: Docker (115) es donde corre Antigravity y todos los servicios
- **LXC jellyfin (100)**: Detenido, posiblemente migrado a Docker
- **Dos NVMe en mirror**: Buena redundancia para el sistema y VMs críticas

---

## 📜 Historial de Cambios

| Fecha | Cambio | Notas |
|-------|--------|-------|
| 2025-12-25 | Documentación completa inicial | Datos extraídos vía SSH por Antigravity |
