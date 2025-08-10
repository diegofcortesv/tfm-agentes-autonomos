#!/usr/bin/env python3
"""
Script para crear todos los archivos de configuración necesarios
"""

import os

def create_setup_scripts():
    """Crea todos los scripts de configuración"""
    
    # Script 1: Setup GCP Project
    gcp_setup_script = '''#!/bin/bash
# Script para configurar proyecto GCP
set -e  # Parar si hay error

# Variables del proyecto
PROJECT_ID="customer-service-agents-tfm"
REGION="us-central1"
ZONE="us-central1-a"

echo "=== Configurando Proyecto GCP para TFM Agentes Autónomos ==="

# 1. Crear proyecto (si no existe)
echo "1. Verificando/creando proyecto..."
if ! gcloud projects describe $PROJECT_ID >/dev/null 2>&1; then
    echo "Creando proyecto $PROJECT_ID..."
    gcloud projects create $PROJECT_ID --name="TFMAgentesAutonomos"
    echo "✅ Proyecto creado"
else
    echo "✅ Proyecto ya existe"
fi

# 2. Configurar proyecto activo
gcloud config set project $PROJECT_ID

# 3. Habilitar facturación (manual)
echo "⚠️  IMPORTANTE: Habilita facturación manualmente en:"
echo "   https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
echo "   Presiona ENTER cuando hayas habilitado facturación..."
read -p ""

# 4. Habilitar APIs necesarias
echo "2. Habilitando APIs de GCP..."
gcloud services enable \\
    sqladmin.googleapis.com \\
    compute.googleapis.com \\
    aiplatform.googleapis.com \\
    storage.googleapis.com \\
    secretmanager.googleapis.com \\
    cloudbuild.googleapis.com \\
    run.googleapis.com

# 5. Configurar región por defecto
echo "3. Configurando región por defecto..."
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# 6. Crear service account para la aplicación
echo "4. Creando service account..."
if ! gcloud iam service-accounts describe customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com >/dev/null 2>&1; then
    gcloud iam service-accounts create customer-service-agent \\
        --display-name="Customer Service Agent TFM" \\
        --description="Service account para agentes autónomos TFM"
    echo "✅ Service account creado"
else
    echo "✅ Service account ya existe"
fi

# 7. Asignar roles necesarios al service account
echo "5. Asignando permisos..."
gcloud projects add-iam-policy-binding $PROJECT_ID \\
    --member="serviceAccount:customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com" \\
    --role="roles/cloudsql.client" \\
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \\
    --member="serviceAccount:customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com" \\
    --role="roles/aiplatform.user" \\
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \\
    --member="serviceAccount:customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com" \\
    --role="roles/storage.objectAdmin" \\
    --quiet

# 8. Crear y descargar clave del service account
echo "6. Generando clave del service account..."
if [ ! -f "gcp-credentials.json" ]; then
    gcloud iam service-accounts keys create ./gcp-credentials.json \\
        --iam-account=customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com
    echo "✅ Clave del service account guardada en gcp-credentials.json"
else
    echo "✅ Archivo de credenciales ya existe"
fi

echo ""
echo "=== Configuración GCP completada ==="
echo "Proyecto: $PROJECT_ID"
echo "Región: $REGION"
echo "Service Account: customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com"
echo ""
echo "🚀 Siguiente paso: Ejecutar ./setup_cloudsql.sh"
'''

    # Script 2: Setup Cloud SQL
    cloudsql_setup_script = '''#!/bin/bash
# Script para configurar Cloud SQL con PostgreSQL y pgvector
set -e

# Variables
PROJECT_ID="customer-service-agents-tfm"
INSTANCE_NAME="customer-service-db"
DB_NAME="customer_service"
DB_USER="app_user"
REGION="us-central1"

echo "=== Configurando Cloud SQL PostgreSQL ==="

# 1. Crear instancia Cloud SQL
echo "1. Creando instancia Cloud SQL..."
if ! gcloud sql instances describe $INSTANCE_NAME >/dev/null 2>&1; then
    echo "Creando instancia $INSTANCE_NAME..."
    gcloud sql instances create $INSTANCE_NAME \\
        --database-version=POSTGRES_15 \\
        --tier=db-f1-micro \\
        --region=$REGION \\
        --storage-type=SSD \\
        --storage-size=20GB \\
        --storage-auto-increase \\
        --backup-start-time=03:00 \\
        --maintenance-window-day=SUN \\
        --maintenance-window-hour=04 \\
        --database-flags=cloudsql.iam_authentication=on
    echo "✅ Instancia Cloud SQL creada"
else
    echo "✅ Instancia Cloud SQL ya existe"
fi

# 2. Configurar contraseña para usuario postgres
echo "2. Configurando contraseña root..."
ROOT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
gcloud sql users set-password postgres \\
    --instance=$INSTANCE_NAME \\
    --password=$ROOT_PASSWORD \\
    --quiet

# 3. Crear base de datos
echo "3. Creando base de datos..."
if ! gcloud sql databases describe $DB_NAME --instance=$INSTANCE_NAME >/dev/null 2>&1; then
    gcloud sql databases create $DB_NAME --instance=$INSTANCE_NAME
    echo "✅ Base de datos creada"
else
    echo "✅ Base de datos ya existe"
fi

# 4. Crear usuario de aplicación
echo "4. Creando usuario de aplicación..."
APP_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
if ! gcloud sql users describe $DB_USER --instance=$INSTANCE_NAME >/dev/null 2>&1; then
    gcloud sql users create $DB_USER \\
        --instance=$INSTANCE_NAME \\
        --password=$APP_PASSWORD
    echo "✅ Usuario de aplicación creado"
else
    echo "✅ Usuario de aplicación ya existe"
fi

# 5. Obtener información de conexión
echo "5. Obteniendo información de conexión..."
CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format="value(connectionName)")
PUBLIC_IP=$(gcloud sql instances describe $INSTANCE_NAME --format="value(ipAddresses[0].ipAddress)")

# 6. Guardar configuración en archivo
cat > database_config.env << EOF
# Configuración Cloud SQL - GENERADO AUTOMÁTICAMENTE
DB_CONNECTION_NAME=$CONNECTION_NAME
DB_HOST=$PUBLIC_IP
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$APP_PASSWORD
DB_ROOT_PASSWORD=$ROOT_PASSWORD
EOF

# 7. Actualizar archivo .env.gcp
if [ -f ".env.gcp" ]; then
    # Crear backup
    cp .env.gcp .env.gcp.backup
    
    # Actualizar variables de BD
    sed -i "s|DB_CONNECTION_NAME=.*|DB_CONNECTION_NAME=$CONNECTION_NAME|" .env.gcp
    sed -i "s|DB_HOST=.*|DB_HOST=$PUBLIC_IP|" .env.gcp
    sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$APP_PASSWORD|" .env.gcp
    echo "✅ Archivo .env.gcp actualizado"
fi

echo ""
echo "=== Configuración Cloud SQL completada ==="
echo "Connection Name: $CONNECTION_NAME"
echo "Public IP: $PUBLIC_IP"
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo ""
echo "📋 IMPORTANTE:"
echo "1. Configuración guardada en: database_config.env"
echo "2. Para habilitar pgvector, ejecuta:"
echo "   ./enable_pgvector.sh"
echo ""
echo "🚀 Siguiente paso: ./enable_pgvector.sh"
'''

    # Script 3: Habilitar pgvector
    enable_pgvector_script = '''#!/bin/bash
# Script para habilitar extensión pgvector
set -e

# Variables
INSTANCE_NAME="customer-service-db"
DB_NAME="customer_service"

echo "=== Habilitando extensión pgvector ==="

# Cargar configuración
if [ -f "database_config.env" ]; then
    source database_config.env
else
    echo "❌ No se encontró database_config.env"
    echo "   Ejecuta primero: ./setup_cloudsql.sh"
    exit 1
fi

echo "1. Conectando a Cloud SQL para habilitar pgvector..."
echo "   Se abrirá una consola PostgreSQL"
echo "   Ejecuta estos comandos:"
echo "   \\c $DB_NAME"
echo "   CREATE EXTENSION IF NOT EXISTS vector;"
echo "   SELECT extname FROM pg_extension WHERE extname = 'vector';"
echo "   \\q"
echo ""
echo "Presiona ENTER para continuar..."
read -p ""

# Conectar a la instancia
gcloud sql connect $INSTANCE_NAME --user=postgres

echo ""
echo "✅ Si viste 'vector' en la consulta, pgvector está habilitado"
echo ""
echo "🚀 Siguiente paso: python project_structure.py"
'''

    # Crear los archivos
    scripts = {
        'setup_gcp_project.sh': gcp_setup_script,
        'setup_cloudsql.sh': cloudsql_setup_script,
        'enable_pgvector.sh': enable_pgvector_script
    }
    
    for filename, content in scripts.items():
        with open(filename, 'w') as f:
            f.write(content)
        os.chmod(filename, 0o755)  # Hacer ejecutable
    
    print("✅ Scripts de configuración creados:")
    for filename in scripts.keys():
        print(f"   - {filename}")

if __name__ == "__main__":
    create_setup_scripts()
    
    print("\n🚀 Scripts listos para ejecutar")
    print("\nOrden de ejecución:")
    print("1. ./setup_gcp_project.sh")
    print("2. ./setup_cloudsql.sh")
    print("3. ./enable_pgvector.sh")
    print("4. python project_structure.py")