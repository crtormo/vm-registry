---
ip: 192.168.100.232
hostname: proxmox-backup-server
type: container
description: Servidor de backups de Proxmox
tags:
  - backup
  - infrastructure
specs:
  cpu: "2 cores"
  ram: "2GB"
  storage: "10GB"
critical: true
ctid: 101
---
# 🔒 Proxmox Backup Server (PBS)

> **Tipo**: LXC Container  
> **CTID**: 101  
> **Estado**: 🟢 Running  
> **Última actualización**: 2025-12-29

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Hostname** | proxmox-backup-server |
| **CTID** | 101 |
| **SO** | Debian |
| **Propósito** | Servidor de backups de Proxmox |

---

## 💻 Recursos

| Recurso | Valor |
|---------|-------|
| **CPU** | 2 cores |
| **RAM** | 2 GB |
| **Disco** | 10 GB |
| **Storage** | Disco-HD |

---

## 🌐 Red

| Campo | Valor |
|-------|-------|
| **IP** | 192.168.100.232 |
| **MAC** | BC:24:11:BA:31:F3 |
| **Bridge** | vmbr0 |

---

## 🔌 Servicios

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 8007 | PBS Web UI | https://192.168.100.232:8007 |
| 22 | SSH | Acceso remoto |

---

## 🔗 Relaciones

```
┌─────────────────┐         ┌─────────────────┐
│ 🖥️ Proxmox VE  │────────►│ 🔒 PBS Server   │
│ (Hypervisor)    │ Backups │ LXC 101         │
└─────────────────┘         └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │ 💾 PBS-NAS      │
                            │ Storage Remoto  │
                            │ (NAS Synology)  │
                            └─────────────────┘
```

---

## 📋 Configuración de Backups

| Aspecto | Valor |
|---------|-------|
| **Datastore** | PBS-NAS (remoto) |
| **Retención** | (Por documentar) |
| **Schedule** | (Por documentar) |
| **VMs incluidas** | (Por documentar) |

---

## 📝 Notas

- Este LXC corre PBS para backup de todas las VMs
- Los backups se almacenan en NAS Synology via PBS-NAS datastore
- Acceso web: https://192.168.100.232:8007

---

## 📜 Historial

| Fecha | Cambio |
|-------|--------|
| 2025-12-25 | Registro creado |
