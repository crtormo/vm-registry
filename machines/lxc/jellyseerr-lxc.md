---
ip: 192.168.100.226
hostname: jellyseerr
type: container
description: Gestor de solicitudes de media
tags:
  - media
  - entertainment
specs:
  cpu: "4 cores"
  ram: "4GB"
  storage: "8GB"
critical: false
ctid: 105
---
# 🎬 Jellyseerr

> **Tipo**: LXC Container  
> **CTID**: 105  
> **Estado**: 🟢 Running  
> **Última actualización**: 2025-12-29

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Hostname** | jellyseerr |
| **CTID** | 105 |
| **SO** | Debian |
| **Propósito** | Gestor de solicitudes de media |

---

## 💻 Recursos

| Recurso | Valor |
|---------|-------|
| **CPU** | 4 cores |
| **RAM** | 4 GB |
| **Disco** | 8 GB |
| **Storage** | local-zfs |

---

## 🌐 Red

| Campo | Valor |
|-------|-------|
| **IP** | 192.168.100.226 |
| **MAC** | BC:24:11:EF:AC:78 |
| **Bridge** | vmbr0 |

---

## 🔌 Servicios

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 5055 | Jellyseerr | http://192.168.100.226:5055 |
| 22 | SSH | Acceso remoto |

---

## 🎬 Funcionalidad

Jellyseerr permite a los usuarios:
- 📺 Solicitar series de TV
- 🎥 Solicitar películas
- 👤 Gestionar usuarios y permisos
- 📊 Ver estado de solicitudes

---

## 🔗 Integraciones

```
┌─────────────────┐
│ 👤 Usuarios     │
│ (Web/App)       │
└────────┬────────┘
         │
┌────────▼────────┐
│ 🎬 Jellyseerr   │
│ LXC 105         │
│ .100.226:5055   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ Sonarr│ │ Radarr│  (Docker VM 115)
│ Series│ │ Pelis │
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
    ┌────▼────┐
    │ Prowlarr│  (Docker VM 115)
    │ Indexers│
    └────┬────┘
         │
    ┌────▼────┐
    │qBittor. │  (Docker VM 115)
    │Downloads│
    └─────────┘
```

---

## ⚙️ Configuración (Por documentar)

| Aspecto | Valor |
|---------|-------|
| **Sonarr URL** | http://192.168.100.209:8989 |
| **Radarr URL** | http://192.168.100.209:7878 |
| **Auth** | (Tipo de auth) |

---

## 📝 Notas

- Recursos generosos (4GB RAM, 4 cores) para buen rendimiento
- Considerar backup de base de datos de solicitudes

---

## 📜 Historial

| Fecha | Cambio |
|-------|--------|
| 2025-12-25 | Registro creado |
