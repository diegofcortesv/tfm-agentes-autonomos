#!/bin/bash
# Script para conectar el Cloud SQL Proxy para el desarrollo local.
# DEJA ESTA TERMINAL ABIERTA mientras trabajas en la aplicación.

set -e

echo "  Iniciando Cloud SQL Proxy para desarrollo..."

# 1. Ir a la raíz del proyecto para encontrar .env y el ejecutable del proxy
cd "$(dirname "$0")/.."

# 2. Cargar las variables de entorno desde .env
if [ -f ".env" ]; then
    source .env
else
    echo "  No se encontró el archivo .env. Asegúrate de estar en la raíz del proyecto."
    exit 1
fi

# 3. Verificar que el proxy existe
if [ ! -f "bin/cloud-sql-proxy" ]; then
    echo "   No se encontró el ejecutable del Cloud SQL Proxy en ./bin/"
    echo "   Ejecuta 'scripts/03_run_proxy_and_init_db.sh' una vez para instalarlo."
    exit 1
fi

# 4. Ejecutar el proxy en primer plano (para ver los logs y poder detenerlo con Ctrl+C)
echo "   Conectando a la instancia: $DB_CONNECTION_NAME en el puerto $PROXY_PORT"
echo "   ==================================================================="
echo "   ¡Conexión lista! Deja esta terminal abierta."
echo "   Ahora, abre OTRA terminal para ejecutar tus scripts de Python."
echo "   ==================================================================="

./bin/cloud-sql-proxy $DB_CONNECTION_NAME --port=$PROXY_PORT --credentials-file=gcp-credentials.json