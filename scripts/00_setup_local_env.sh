#!/bin/bash
# Script de configuración rápida del entorno de desarrollo

echo " Configuración Rápida - TFM Agentes Autónomos"


# Verificar si estamos en el directorio correcto
if [ ! -f "README.md" ]; then
    echo " Creando directorio del proyecto..."
    mkdir -p tfm-agentes-autonomos
    cd tfm-agentes-autonomos
fi

# 1. Verificar Python
echo " Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
    echo " Python encontrado: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version | cut -d " " -f 2)
    echo " Python encontrado: $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    echo "Python no encontrado. Por favor instala Python 3.9+"
    exit 1
fi

# 2. Crear entorno virtual
echo " Creando entorno virtual..."
if [ ! -d "venv_tfm_agents" ]; then
    $PYTHON_CMD -m venv venv_tfm_agents
    echo "Entorno virtual creado"
else
    echo "Entorno virtual ya existe"
fi

# 3. Activar entorno virtual
echo "Activando entorno virtual..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv_tfm_agents/Scripts/activate
else
    # Linux/macOS
    source venv_tfm_agents/bin/activate
fi

# 4. Verificar gcloud
echo "  Verificando Google Cloud SDK..."
if command -v gcloud &> /dev/null; then
    GCLOUD_VERSION=$(gcloud --version | head -n 1)
    echo " $GCLOUD_VERSION"
else
    echo " Google Cloud SDK no encontrado"
    echo " Por favor instala desde: https://cloud.google.com/sdk/docs/install"
    echo "   Luego ejecuta: gcloud auth login"
    exit 1
fi

# 5. Verificar autenticación GCP
echo " Verificando autenticación GCP..."
if gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
    echo " Autenticado como: $ACTIVE_ACCOUNT"
else
    echo " No hay cuenta activa en GCP"
    echo " Ejecutando autenticación..."
    gcloud auth login
    gcloud auth application-default login
fi

# 6. Crear archivos de configuración VSCode
echo "  Configurando VSCode..."
mkdir -p .vscode

cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./venv_tfm_agents/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.formatting.provider": "black",
    "files.associations": {
        "*.yml": "yaml",
        "*.yaml": "yaml"
    }
}
EOF

# 7. Crear .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv_tfm_agents/
.env
.env.local
.env.gcp

# IDEs
.vscode/launch.json
.idea/

# GCP
gcp-credentials.json
database_config.env

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# OS
.DS_Store
Thumbs.db
EOF

# 8. Crear README básico
cat > README.md << 'EOF'

EOF

echo ""
echo " ¡Configuración inicial completada!"
echo "================================================"
echo ""
echo " Próximos pasos:"
echo "1. Abrir VSCode: code ."
echo "2. Seleccionar intérprete Python: Ctrl+Shift+P → 'Python: Select Interpreter'"
echo "3. Elegir: ./venv_tfm_agents/bin/python (o Scripts/python.exe en Windows)"
echo "4. Ejecutar verificación: python verify_environment.py"
echo ""
echo "Una vez configurado VSCode, continúa con los scripts de GCP"