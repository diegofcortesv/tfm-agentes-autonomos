set -e
source ../.env

PROJECT_ID="customer-service-agents-tfm"
INSTANCE_NAME="customer-service-db"
DB_NAME="customer_service"
DB_USER="app_user"
REGION="us-central1"

echo "Configurando Cloud SQL PostgreSQL"

# 1. Crear instancia
echo "1. Creando instancia Cloud SQL..."
if ! gcloud sql instances describe $INSTANCE_NAME >/dev/null 2>&1; then
    gcloud sql instances create $INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-type=SSD \
        --storage-size=20GB \
        --storage-auto-increase
    echo "Instancia creada"
else
    echo "Instancia ya existe"
fi

# 2. Contraseña root
echo "2. Configurando contraseña..."
ROOT_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
gcloud sql users set-password postgres \
    --instance=$INSTANCE_NAME \
    --password=$ROOT_PASSWORD --quiet

# 3. Crear base de datos
echo "3. Creando base de datos..."
if ! gcloud sql databases describe $DB_NAME --instance=$INSTANCE_NAME >/dev/null 2>&1; then
    gcloud sql databases create $DB_NAME --instance=$INSTANCE_NAME
    echo "Base de datos creada"
fi

# 4. Usuario de aplicación
echo "4. Creando usuario..."
APP_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
if ! gcloud sql users describe $DB_USER --instance=$INSTANCE_NAME >/dev/null 2>&1; then
    gcloud sql users create $DB_USER \
        --instance=$INSTANCE_NAME \
        --password=$APP_PASSWORD
    echo "Usuario creado"
fi

# 5. Obtener información
CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format="value(connectionName)")
PUBLIC_IP=$(gcloud sql instances describe $INSTANCE_NAME --format="value(ipAddresses[0].ipAddress)")

# 6. Guardar configuración
echo " " >> ../.env
echo "#Configuración Cloud SQL (GENERADO AUTOMÁTICAMENTE)" >> ../.env
echo "DB_CONNECTION_NAME=$CONNECTION_NAME" >> ../.env
echo "DB_ROOT_PASSWORD=$ROOT_PASSWORD" >> ../.env
# Actualizamos la contraseña del usuario de la app que se acaba de crear
sed -i "/^DB_PASSWORD=/c\DB_PASSWORD=$APP_PASSWORD" ../.env

echo "Configuración guardada en el archivo .env principal."