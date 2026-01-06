# 🖥️ Scanner Frontend

Interfaz web para visualizar y controlar el Scanner de Red de VM Registry.

## 🌟 Características

- **Mapa de Red Visual**: Visualización gráfica de la topología de red.
- **Lista de Dispositivos**: Tabla detallada con estado, IP, MAC y detalles de cada dispositivo.
- **Control de Escaneo**: Botones para iniciar diferentes tipos de escaneo (Rápido, Completo, etc.).
- **Estado en Tiempo Real**: Indicadores de estado de servicios y conectividad vía WebSockets.
- **Edición**: Capacidad (en desarrollo) para editar metadatos de dispositivos capturados.

## 🛠️ Tecnologías

- **HTML5 / CSS3**: Diseño responsive y moderno.
- **JavaScript (Vanilla)**: Lógica del cliente sin frameworks pesados.
- **Vis.js**: Para la visualización de grafos de red.
- **Nginx**: Servidor web ligero para servir los archivos estáticos.

## 🔌 Conexión con Backend

El frontend se conecta al backend a través de:
- **API REST**: Para comandos y recuperación de datos históricos.
- **WebSocket**: `ws://<host>:8000/ws` para actualizaciones en vivo.

## 🚀 Despliegue

Se despliega automáticamente junto con el stack principal mediante Docker Compose:

```bash
docker compose up -d scanner-ui
```

El servidor Nginx en el contenedor expone el puerto 80 (mapeado según configuración en `docker-compose.yml`, típicamente usa `network_mode: host` o un puerto específico).
