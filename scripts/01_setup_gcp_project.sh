# Script para configurar proyecto GCP
set -e
source ../.env 

PROJECT_ID="customer-service-agents-tfm"
REGION="us-central1"
ZONE="us-central1-a"

echo "Configurando Proyecto GCP para TFM Agentes Autónomos"

# 1. Crear proyecto (si no existe)
echo "1. Verificando/creando proyecto..."
if ! gcloud projects describe $PROJECT_ID >/dev/null 2>&1; then
    echo "Creando proyecto $PROJECT_ID..."
    gcloud projects create $PROJECT_ID --name="TFMAgentesAutonomos"
    echo "Proyecto creado"
else
    echo "Proyecto ya existe"
fi

# 2. Configurar proyecto activo
gcloud config set project $PROJECT_ID

# 3. Habilitar facturación (manual)
echo "IMPORTANTE: Habilita facturación manualmente en:"
echo "   https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
echo "   Presiona ENTER cuando hayas habilitado facturación..."
read -p ""

# 4. Habilitar APIs
echo "2. Habilitando APIs de GCP..."
gcloud services enable \
    sqladmin.googleapis.com \
    compute.googleapis.com \
    aiplatform.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com

# 5. Configurar región
echo "3. Configurando región por defecto..."
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# 6. Crear service account
echo "4. Creando service account..."
if ! gcloud iam service-accounts describe customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com >/dev/null 2>&1; then
    gcloud iam service-accounts create customer-service-agent \
        --display-name="Customer Service Agent TFM"
    echo "Service account creado"
else
    echo "Service account ya existe"
fi

# 7. Asignar permisos
echo "5. Asignando permisos..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client" --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user" --quiet

# 8. Crear clave
echo "6. Generando clave del service account..."
if [ ! -f "gcp-credentials.json" ]; then
    gcloud iam service-accounts keys create ./gcp-credentials.json \
        --iam-account=customer-service-agent@$PROJECT_ID.iam.gserviceaccount.com
    echo "Clave guardada en gcp-credentials.json"
fi

echo ""
echo "Configuración GCP completada!"