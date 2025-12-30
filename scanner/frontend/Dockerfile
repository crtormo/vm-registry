FROM nginx:alpine

# Copiar archivos estáticos
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY main.js /usr/share/nginx/html/

# Copiar configuración Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Puerto
EXPOSE 3080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD wget --quiet --tries=1 --spider http://localhost:3080/health || exit 1
