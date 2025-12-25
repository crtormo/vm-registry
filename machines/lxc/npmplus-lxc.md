# 🌐 NPMplus (Nginx Proxy Manager Plus)

> **Tipo**: LXC Container  
> **CTID**: 106  
> **Estado**: 🟢 Running  
> **Última actualización**: 2025-12-25

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Hostname** | npmplus |
| **CTID** | 106 |
| **SO** | Alpine Linux |
| **Propósito** | Reverse Proxy + SSL + Routing |

---

## 💻 Recursos

| Recurso | Valor |
|---------|-------|
| **CPU** | 1 core |
| **RAM** | 512 MB |
| **Disco** | 3 GB |
| **Storage** | local-zfs |

---

## 🌐 Red

| Campo | Valor |
|-------|-------|
| **IP** | 192.168.100.220 |
| **MAC** | BC:24:11:B8:AE:DF |
| **Bridge** | vmbr0 |

---

## 🔌 Servicios

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 80 | HTTP | Redirección a HTTPS |
| 443 | HTTPS | Tráfico SSL |
| 81 | Admin UI | Panel de administración |

---

## 🔗 Proxies Configurados (Por documentar)

| Dominio | Destino | SSL |
|---------|---------|-----|
| (Documentar) | (Destino) | ✅/❌ |

---

## 📊 Arquitectura

```
                         ┌─────────────────┐
                         │    INTERNET     │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │  🌐 NPMplus     │
                         │  LXC 106        │
                         │  .100.220       │
                         │  :80 :443       │
                         └────────┬────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼───────┐        ┌───────▼───────┐        ┌───────▼───────┐
│ 📚 MedFlix    │        │ 👤 LifeCRM    │        │ 🎬 Jellyseerr │
│ Docker:3000   │        │ Docker:8000   │        │ LXC:5055      │
└───────────────┘        └───────────────┘        └───────────────┘
```

---

## 🔒 SSL/Certificados

| Aspecto | Valor |
|---------|-------|
| **Proveedor** | Let's Encrypt |
| **Tipo** | Wildcard / Individual |
| **Renovación** | Automática |

---

## ⚡ Rol en la Infraestructura

NPMplus actúa como punto de entrada único para todos los servicios web:
- ✅ Terminación SSL centralizada
- ✅ Routing basado en dominio/subdomain
- ✅ Caché y compresión
- ✅ Headers de seguridad

---

## 📝 Notas

- Alpine Linux = mínimo footprint (512MB RAM)
- NPMplus es un fork mejorado de Nginx Proxy Manager
- Panel admin en puerto 81

---

## 📜 Historial

| Fecha | Cambio |
|-------|--------|
| 2025-12-25 | Registro creado |
