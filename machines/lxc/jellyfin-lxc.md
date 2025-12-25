# 🎬 Jellyfin (DETENIDO)

> **Tipo**: LXC Container  
> **CTID**: 100  
> **Estado**: 🔴 Stopped  
> **Última actualización**: 2025-12-25

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Hostname** | jellyfin |
| **CTID** | 100 |
| **SO** | Ubuntu |
| **Propósito** | Media Server (actualmente deshabilitado) |
| **Lock** | snapshot |

---

## 💻 Recursos Asignados

| Recurso | Valor |
|---------|-------|
| **CPU** | 2 cores |
| **RAM** | 2 GB |
| **Disco** | 16 GB |
| **Storage** | local-zfs |

---

## 🌐 Red (cuando activo)

| Campo | Valor |
|-------|-------|
| **IP** | DHCP |
| **MAC** | BC:24:11:D9:DF:69 |
| **Bridge** | vmbr0 |

---

## ⚠️ Estado Actual

```
┌─────────────────────────────────────────────────────────────┐
│                    ⚠️ CONTENEDOR DETENIDO                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Este LXC está DETENIDO y tiene un lock de snapshot.        │
│                                                             │
│  Posibles razones:                                          │
│  - Migrado a Docker (Jellyfin en VM 115?)                   │
│  - Reemplazado por otra solución                           │
│  - En proceso de migración/backup                          │
│                                                             │
│  Acción recomendada:                                        │
│  - Verificar si hay Jellyfin corriendo en Docker            │
│  - Si está duplicado, considerar eliminar este LXC          │
│  - Liberar espacio en local-zfs (16GB)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Investigación Pendiente

- [ ] ¿Existe Jellyfin en Docker VM?
- [ ] ¿Por qué tiene lock de snapshot?
- [ ] ¿Se puede eliminar este LXC?
- [ ] ¿Hay datos importantes que migrar?

---

## 📝 Notas

- CTID 100 = primer contenedor creado (legacy)
- 16GB de disco ocupando espacio en NVMe (local-zfs)
- Considerar limpieza si ya no se necesita

---

## 📜 Historial

| Fecha | Cambio |
|-------|--------|
| 2025-12-25 | Registro creado - estado detenido |
