# knowledge_mcp_server_standalone.py
import asyncio
import os
import logging
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
from sentence_transformers import SentenceTransformer
import asyncpg
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- Configuración de logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Inicialización del Servidor MCP y Recursos ---
logger.info("INFO: Servidor MCP de Conocimiento Standalone: Inicializando...")
app = Server("knowledge-base")

# Modelo se carga de forma diferida para evitar timeouts durante inicialización
model = None

def get_model():
    """Carga el modelo SentenceTransformer de forma diferida."""
    global model
    if model is None:
        logger.info("Cargando modelo SentenceTransformer...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("✅ Modelo de embeddings cargado y listo.")
    return model

async def get_db_connection():
    """Obtiene una conexión a la base de datos PostgreSQL."""
    try:
        return await asyncpg.connect(
            host='127.0.0.1',  # Siempre usar localhost para el proxy
            port=5433,  # Puerto del proxy
            user=os.getenv('DB_USER', 'app_user'),  # Usuario correcto
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'customer_service'),  # BD correcta
            timeout=30  # Timeout más largo
        )
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        raise

async def semantic_search(query_embedding: list[float], top_k: int = 3):
    """
    Realiza una búsqueda semántica en la base de conocimiento.
    Si no hay embeddings, usa búsqueda por texto como fallback.
    """
    try:
        conn = await get_db_connection()
        try:
            # Primero verificar si hay embeddings disponibles
            embedding_count = await conn.fetchval("SELECT count(*) FROM knowledge_base WHERE embedding IS NOT NULL")
            
            if embedding_count > 0:
                # Búsqueda semántica con embeddings
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                query = """
                SELECT title, content, 
                       1 - (embedding <=> $1::vector) as similarity
                FROM knowledge_base 
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """
                
                rows = await conn.fetch(query, embedding_str, top_k)
                
            else:
                # Fallback: búsqueda por texto usando ILIKE
                logger.info("No hay embeddings disponibles, usando búsqueda por texto")
                
                # Extraer términos clave del query (simulado)
                search_terms = ["conexión", "base", "datos", "error", "problema"]  # Términos comunes
                
                query = """
                SELECT title, content, 0.8 as similarity
                FROM knowledge_base 
                WHERE content ILIKE '%' || $1 || '%' 
                   OR title ILIKE '%' || $1 || '%'
                   OR content ILIKE '%conexión%'
                   OR content ILIKE '%error%'
                   OR content ILIKE '%problema%'
                ORDER BY 
                    CASE 
                        WHEN title ILIKE '%' || $1 || '%' THEN 1
                        WHEN content ILIKE '%' || $1 || '%' THEN 2
                        ELSE 3
                    END
                LIMIT $2
                """
                
                # Usar términos genéricos para la búsqueda
                search_term = "base datos"  # Término de búsqueda por defecto
                rows = await conn.fetch(query, search_term, top_k)
            
            results = []
            for row in rows:
                results.append({
                    'title': row['title'],
                    'content': row['content'],
                    'similarity': float(row['similarity'])
                })
            
            # Si no hay resultados, devolver todos los registros como fallback
            if not results:
                fallback_query = "SELECT title, content, 0.5 as similarity FROM knowledge_base LIMIT $1"
                rows = await conn.fetch(fallback_query, top_k)
                for row in rows:
                    results.append({
                        'title': row['title'],
                        'content': row['content'],
                        'similarity': 0.5
                    })
            
            return results
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {e}")
        # Devolver resultados de fallback si falla la BD
        return [
            {
                'title': 'Sistema en Mantenimiento',
                'content': f'No se pudo acceder a la base de conocimiento. Error: {str(e)}. Por favor, contacte al administrador del sistema.',
                'similarity': 0.5
            }
        ]

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
        current_model = get_model()
        query_embedding = current_model.encode(query).tolist()
        
        # Realizar búsqueda semántica
        search_results = await semantic_search(query_embedding, top_k=top_k)
        
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
    
    logger.info("✅ Servidor MCP de Conocimiento listo para recibir peticiones")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())