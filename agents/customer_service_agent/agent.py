# agents/customer_service_agent/agent.py
import sys
import os
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Importar el agente desde la ubicación original
from customer_service_agent_app.agent import root_agent

# Exportar para ADK
__all__ = ["root_agent"]
