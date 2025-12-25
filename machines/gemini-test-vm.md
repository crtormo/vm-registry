# 🧪 Gemini Test VM

> **Tipo**: VM (QEMU)  
> **VMID**: 200  
> **Estado**: 🟢 Running  
> **Última actualización**: 2025-12-25

---

## 📊 Información General

| Campo | Valor |
|-------|-------|
| **Nombre** | gemini-test |
| **VMID** | 200 |
| **SO** | Linux (l26) |
| **Propósito** | Testing y desarrollo experimental |
| **Autostart** | ✅ Sí |
| **Firewall** | ✅ Habilitado |

---

## 💻 Recursos Asignados

| Recurso | Valor |
|---------|-------|
| **CPU** | 4 cores |
| **RAM** | 16 GB |
| **Disco** | 100 GB |
| **Storage** | Disco-HD (HDD, qcow2) |
| **Controlador** | virtio-scsi-single + iothread |

---

## 🌐 Red

| Campo | Valor |
|-------|-------|
| **IP** | DHCP |
| **MAC** | BC:24:11:D0:6C:D0 |
| **Bridge** | vmbr0 |
| **Interfaz** | virtio |

---

## 🔬 Uso Previsto

Esta VM está destinada a:
- 🧪 Pruebas de nuevas configuraciones
- 🔬 Desarrollo experimental
- 🤖 Testing de modelos AI/Gemini
- 📦 Sandbox para nuevos proyectos

---

## ⚠️ Notas

- **Almacenamiento en HDD**: Más lento que VM 115 (NVMe)
- **No producción**: Esta VM es para testing, no correr servicios críticos
- **Recursos generosos**: 16GB RAM para experimentos intensivos

---

## 🔗 Relaciones

```
┌─────────────────┐
│ 🧪 Gemini Test  │
│ VM 200          │
│ (Sandbox)       │
└────────┬────────┘
         │
         └──────► 🐳 Docker VM 115
                  (Puede replicar configs)
```

---

## 📜 Historial

| Fecha | Cambio |
|-------|--------|
| 2025-12-25 | Registro creado |
