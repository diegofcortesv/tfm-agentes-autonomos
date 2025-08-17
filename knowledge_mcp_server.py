# knowledge_mcp_server.py
import asyncio
import sys
import os
from mcp.server import Server
from mcp.types import Tool, TextContent
from sentence_transformers import SentenceTransformer
from typing import Any, Sequence
import logging

# Añade la ruta del proyecto para poder importar los módulos de la app
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importar directamente los componentes necesarios para evitar dependencias circulares
def get_knowledge_repository():
    """
    Función para importar KnowledgeRepository solo cuando se necesite,
    evitando dependencias circulares durante la inicialización.
    """
    from customer_service_agent_app.repository.knowledge_repository import KnowledgeRepository
    return KnowledgeRepository()

# --- Configuración de logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Inicialización del Servidor MCP y Recursos ---
logger.info("INFO: Servidor MCP de Conocimiento: Inicializando...")
app = Server("knowledge-base")
model = SentenceTransformer('all-MiniLM-L6-v2')
logger.info("Servidor MCP de Conocimiento: Modelo de embeddings cargado y listo.")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Lista las herramientas disponibles en este servidor MCP.
    """
    return [
        Tool(
            name="search_knowledge",
            description="Busca información relevante en la base de conocimiento usando búsqueda semántica",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La consulta o pregunta para buscar en la base de conocimiento"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Número máximo de resultados a devolver",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """
    Ejecuta la herramienta especificada con los argumentos dados.
    """
    if name != "search_knowledge":
        raise ValueError(f"Herramienta desconocida: {name}")
    
    try:
        query = arguments["query"]
        top_k = arguments.get("top_k", 3)
        
        logger.info(f"INFO: Servidor MCP recibió la consulta: '{query}'")
        
        # Generar embedding de la consulta
        query_embedding = model.encode(query).tolist()
        
        # Obtener repositorio y realizar búsqueda semántica
        repository = get_knowledge_repository()
        search_results = await repository.semantic_search(query_embedding, top_k=top_k)
        
        if not search_results:
            return [TextContent(
                type="text",
                text="No se encontraron soluciones relevantes en la base de conocimiento."
            )]
        
        # Formatear resultados
        formatted_context = "\n---\n".join([
            f"Título: {result['title']}\nContenido: {result['content']}\nRelevancia: {result['similarity']:.2f}"
            for result in search_results
        ])
        
        return [TextContent(
            type="text",
            text=f"Información encontrada en la base de conocimiento:\n\n{formatted_context}"
        )]
        
    except Exception as e:
        logger.error(f"ERROR: Servidor MCP de Conocimiento: {e}")
        return [TextContent(
            type="text", 
            text=f"Error al buscar en la base de conocimiento: {str(e)}"
        )]

async def main():
    """
    Función principal para ejecutar el servidor MCP.
    """
    from mcp.server.stdio import stdio_server
    
    logger.info("Servidor MCP de Conocimiento listo para recibir peticiones")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())