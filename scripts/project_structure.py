# Script para crear estructura de proyecto actualizada
import os

def create_project_structure():
    """Crea la estructura de carpetas para el proyecto con BD y MCP"""
    
    structure = {
        "customer_service_agent_app": {
            "config": {
                "__init__.py": "",
                "database.py": "# Configuración de base de datos",
                "gcp.py": "# Configuración GCP",
                "settings.py": "# Settings generales"
            },
            "database": {
                "__init__.py": "",
                "models.py": "# Modelos SQLAlchemy",
                "connection.py": "# Pool de conexiones",
                "repositories": {
                    "__init__.py": "",
                    "customer_repository.py": "",
                    "interaction_repository.py": "",
                    "knowledge_repository.py": ""
                },
                "migrations": {
                    "__init__.py": "",
                    "env.py": "# Alembic config"
                }
            },
            "mcp": {
                "__init__.py": "",
                "knowledge_server.py": "# MCP Server implementation",
                "vector_search.py": "# Búsqueda vectorial",
                "rag_pipeline.py": "# RAG implementation",
                "tools.py": "# MCP tools"
            },
            "subagents": {
                "__init__.py": "",
                "context_analyzer_agent": {
                    "__init__.py": "",
                    "agent.py": "# Agent con DB integration",
                    "tools.py": "# Tools con BD",
                    "repository.py": "# Data access layer"
                },
                "knowledge_agent": {
                    "__init__.py": "",
                    "agent.py": "# Agent con MCP",
                    "mcp_tools.py": "# MCP tools",
                    "semantic_search.py": "# Vector search"
                },
                "sentiment_agent": {
                    "__init__.py": "",
                    "agent.py": "",
                    "tools.py": "# Tools con cache BD"
                },
                "priority_agent": {
                    "__init__.py": "",
                    "agent.py": "",
                    "tools.py": "# Tools con reglas en BD"
                },
                "response_synthesizer": {
                    "__init__.py": "",
                    "agent.py": ""
                }
            },
            "utils": {
                "__init__.py": "",
                "logging.py": "# Logging configuration",
                "metrics.py": "# Metrics collection",
                "cache.py": "# Redis cache (opcional)"
            },
            "tests": {
                "__init__.py": "",
                "test_database.py": "",
                "test_mcp.py": "",
                "test_agents.py": ""
            },
            "scripts": {
                "init_db.py": "# Script inicialización BD",
                "migrate_data.py": "# Migración datos existentes",
                "setup_vectors.py": "# Setup vectorial"
            }
        }
    }
    
    def create_structure(base_path, structure_dict):
        for name, content in structure_dict.items():
            path = os.path.join(base_path, name)
            
            if isinstance(content, dict):
                # Es una carpeta
                os.makedirs(path, exist_ok=True)
                create_structure(path, content)
            else:
                # Es un archivo
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content if content else f"# {name}\n")
    
    # Crear estructura
    create_structure(".", structure)
    print("✅ Estructura de proyecto creada exitosamente")
    

if __name__ == "__main__":
    create_project_structure()