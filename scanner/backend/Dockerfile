FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema: arp-scan, nmap, y build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    arp-scan \
    nmap \
    iputils-ping \
    net-tools \
    iproute2 \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Puerto
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
