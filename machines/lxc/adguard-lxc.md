# 🛡️ AdGuard Home

> **Tipo**: LXC Container  
> **CTID**: 103  
> **Estado**: 🟢 Running  
> **Última actualización**: 2025-12-25

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Hostname** | adguard |
| **CTID** | 103 |
| **SO** | Debian |
| **Propósito** | DNS Server + Ad Blocking para toda la red |

---

## 💻 Recursos

| Recurso | Valor |
|---------|-------|
| **CPU** | 1 core |
| **RAM** | 512 MB |
| **Disco** | 2 GB |
| **Storage** | local-zfs |

---

## 🌐 Red

| Campo | Valor |
|-------|-------|
| **IP** | 192.168.100.113 |
| **MAC** | BC:24:11:2E:32:DF |
| **Bridge** | vmbr0 |

---

## 🔌 Servicios

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 53 | DNS | Servidor DNS para toda la red |
| 80 | Web UI | http://192.168.100.113 |
| 22 | SSH | Acceso remoto |

---

## ⚡ Rol Crítico

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO DNS DE LA RED                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   📱 Dispositivos        🛡️ AdGuard           🌐 Internet   │
│   (Toda la red)    ───► LXC 103         ───►  DNS Público  │
│                         Filtrado               (si no está │
│                         de anuncios            bloqueado)  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔗 Relaciones

```
┌─────────────────┐
│ 🔌 Router       │
│ DNS: .100.113   │ ◄── Configurado para usar AdGuard
└────────┬────────┘
         │
┌────────▼────────┐
│ 🛡️ AdGuard     │
│ LXC 103         │
│ .100.113:53     │
└────────┬────────┘
         │
         ├──────► 🐳 Docker VM (.100.209)
         ├──────► 🏠 Home Assistant
         ├──────► 📱 Dispositivos IoT
         └──────► 💻 PCs/Laptops
```

---

## 📊 Estadísticas (Por documentar)

| Métrica | Valor |
|---------|-------|
| Consultas/día | - |
| % Bloqueado | - |
| Listas activas | - |

---

## ⚠️ Notas Críticas

> **IMPORTANTE**: Si este LXC cae, TODA la red pierde resolución DNS.
> Considerar:
> - IP estática (ya configurada ✅)
> - Autostart (verificar)
> - DNS de respaldo en router

---

## 📜 Historial

| Fecha | Cambio |
|-------|--------|
| 2025-12-25 | Registro creado |
