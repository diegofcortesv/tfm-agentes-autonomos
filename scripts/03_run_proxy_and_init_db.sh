# scripts/03_run_proxy_and_init_db.sh
#!/bin/bash
set -e
source ../.env

echo "Conectando y Preparando la Base de Datos"

# 1. Instalar/Verificar el proxy (lógica de setup_cloudsql_proxy.sh)
if [ ! -f "../bin/cloud-sql-proxy" ]; then
    echo "1. Descargando Cloud SQL Proxy..."
    mkdir -p ../bin
    curl -o ../bin/cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
    chmod +x ../bin/cloud-sql-proxy
    echo "Proxy descargado en la carpeta 'bin'."
else
    echo "1. Cloud SQL Proxy ya existe."
fi

# 2. Iniciar el proxy en segundo plano
echo "2. Iniciando Cloud SQL Proxy en puerto $PROXY_PORT..."
# Matar proceso anterior si existe
pkill -f cloud-sql-proxy 2>/dev/null || true
sleep 2

../bin/cloud-sql-proxy $DB_CONNECTION_NAME --port=$PROXY_PORT &
PROXY_PID=$!
echo "   Proxy PID: $PROXY_PID"
sleep 5

# Verificar que el proxy se está ejecutando
if ! kill -0 $PROXY_PID 2>/dev/null; then
    echo "Error al iniciar Cloud SQL Proxy. Verifica las credenciales y la conexión."
    exit 1
fi
echo "Proxy ejecutándose correctamente."

# Función para detener el proxy al salir
cleanup() {
    echo "Deteniendo el Cloud SQL Proxy (PID: $PROXY_PID)..."
    kill $PROXY_PID
}
trap cleanup EXIT # Esto asegura que el proxy se detenga cuando el script termine

# 3. Habilitar pgvector
echo -e "\n3. Habilitando la extensión pgvector..."
python3 ./enable_pgvector.py

# 4. Inicializar las tablas y datos
echo -e "\n4. Creando tablas e insertando datos de ejemplo..."
python3 ./init_database.py

echo -e "\n Base de datos lista y configurada."
echo "   El proxy se detendrá ahora. Para volver a conectarte para desarrollo,"
echo "   ejecuta este comando en una terminal separada:"
echo "   ./scripts/03_run_proxy_and_init_db.sh"