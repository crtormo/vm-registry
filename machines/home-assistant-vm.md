# 🏠 Home Assistant VM

> **Tipo**: VM (QEMU)  
> **VMID**: 111  
> **Estado**: 🟢 Running  
> **Última actualización**: 2025-12-25

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Nombre** | home-assistant |
| **VMID** | 111 |
| **Propósito** | Domótica y automatización del hogar |
| **Autostart** | ✅ Sí |

---

## 💻 Recursos Asignados

| Recurso | Valor |
|---------|-------|
| **CPU** | 2 cores |
| **RAM** | 4 GB |
| **Disco** | 32 GB (SATA) |
| **Storage** | (Por confirmar) |

---

## 🌐 Red

| Campo | Valor |
|-------|-------|
| **IP** | DHCP (Por confirmar IP fija) |
| **MAC** | BC:24:11:D8:EA:E9 |
| **Bridge** | vmbr0 |
| **Interfaz** | virtio |

---

## 🔌 Puertos Expuestos

| Puerto | Servicio | Descripción |
|--------|----------|-------------|
| 8123 | Home Assistant | Interfaz Web |
| 22 | SSH | Acceso remoto |

---

## 🏠 Integraciones Típicas

### Protocolos
- 🔵 Zigbee (via dongle USB o Zigbee2MQTT)
- 🔴 Z-Wave (opcional)
- 📶 WiFi (dispositivos IoT)
- 🌐 MQTT (broker de mensajes)

### Dispositivos (Por documentar)
- Luces inteligentes
- Sensores
- Termostatos
- Cámaras
- Cerraduras

---

## 🔗 Relaciones

```
┌─────────────────┐
│ 🏠 Home         │
│ Assistant       │
│ VM 111          │
└────────┬────────┘
         │
         ├──────► 🔵 Zigbee Devices
         │
         ├──────► 📱 App Móvil (Companion)
         │
         ├──────► 🔧 n8n (Automaciones externas)
         │        (Docker VM 115)
         │
         └──────► 🌐 NPMplus (Acceso externo)
                  (LXC 106)
```

---

## 📝 Notas

- Esta VM corre la instalación principal de Home Assistant
- Considerar backup regular de configuración
- Guest agent: (Por verificar si está instalado)

---

## 📜 Historial

| Fecha | Cambio |
|-------|--------|
| 2025-12-25 | Registro creado |
