# customer_service_agent_app/subagents/knowledge_agent/tools.py

import os
from google.adk.tools import MCPToolset
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

# Obtener la ruta absoluta del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
mcp_server_path = os.path.join(project_root, "knowledge_mcp_server_standalone.py")

# Crear el MCPToolset para conectar con el servidor MCP de conocimiento
knowledge_search_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=[mcp_server_path],
            cwd=project_root
        ),
        timeout=30.0  # Timeout más largo para carga de modelos y BD
    )
)