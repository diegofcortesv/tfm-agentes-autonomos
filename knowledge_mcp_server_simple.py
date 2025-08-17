# knowledge_mcp_server_simple.py
import asyncio
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent

# --- Configuración de logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Inicialización del Servidor MCP Simple ---
logger.info("INFO: Servidor MCP de Conocimiento Simple: Inicializando...")
app = Server("knowledge-base")
logger.info("Servidor MCP de Conocimiento Simple listo.")

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
        
        # Para las pruebas, devolvemos resultados simulados
        mock_results = [
            {
                'title': 'Solución de Problemas Técnicos',
                'content': f'Respuesta simulada para la consulta: {query}. Esta es una respuesta de prueba del sistema MCP.',
                'similarity': 0.95
            },
            {
                'title': 'Procedimiento Estándar',
                'content': 'Este es un resultado de ejemplo que muestra cómo funciona el sistema de búsqueda semántica.',
                'similarity': 0.87
            }
        ]
        
        # Limitar resultados según top_k
        results = mock_results[:top_k]
        
        # Formatear resultados
        formatted_context = "\n---\n".join([
            f"Título: {result['title']}\nContenido: {result['content']}\nRelevancia: {result['similarity']:.2f}"
            for result in results
        ])
        
        return [TextContent(
            type="text",
            text=f"Información encontrada en la base de conocimiento (modo prueba):\n\n{formatted_context}"
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
    
    logger.info("Servidor MCP de Conocimiento Simple listo para recibir peticiones")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())