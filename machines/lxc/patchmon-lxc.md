---
ip: 192.168.100.228
hostname: patchmon
type: container
description: Monitoreo de parches y seguridad
tags:
  - monitoring
  - security
specs:
  cpu: "2 cores"
  ram: "2GB"
  storage: "4GB"
critical: false
ctid: 102
---
# 🔍 Patchmon

> **Tipo**: LXC Container  
> **CTID**: 102  
> **Estado**: 🟢 Running  
> **Última actualización**: 2025-12-29

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Hostname** | patchmon |
| **CTID** | 102 |
| **SO** | Debian |
| **Propósito** | Monitoreo de parches y seguridad |

---

## 💻 Recursos

| Recurso | Valor |
|---------|-------|
| **CPU** | 2 cores |
| **RAM** | 2 GB |
| **Disco** | 4 GB |
| **Storage** | local-zfs |

---

## 🌐 Red

| Campo | Valor |
|-------|-------|
| **IP** | 192.168.100.228 |
| **MAC** | BC:24:11:FE:61:5F |
| **Bridge** | vmbr0 |

---

## 🔌 Servicios

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 22 | SSH | Acceso remoto |
| (Por doc) | Web UI? | Si tiene interfaz web |

---

## 🔒 Funcionalidad

Patchmon se encarga de:
- 🔍 Monitorear actualizaciones pendientes
- 🛡️ Verificar vulnerabilidades conocidas
- 📊 Reportar estado de parches
- ⚠️ Alertar sobre actualizaciones críticas

---

## 🔗 Sistemas Monitoreados (Por documentar)

| Sistema | Tipo | Estado |
|---------|------|--------|
| Proxmox Host | Hypervisor | ✅ |
| Docker VM | VM | ✅ |
| LXC Containers | Container | ✅ |

---

## 📝 Notas

- Disco pequeño (4GB) - solo monitoreo, no almacena mucho
- Verificar qué herramienta específica corre (patch-manager, unattended-upgrades monitor, etc.)

---

## 📜 Historial

| Fecha | Cambio |
|-------|--------|
| 2025-12-25 | Registro creado |
