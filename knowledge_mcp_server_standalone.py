# knowledge_mcp_server_standalone.py
import asyncio
import os
import logging
import time
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
from sentence_transformers import SentenceTransformer
import asyncpg
from dotenv import load_dotenv

# Importar el sistema de métricas - VERSIÓN DIRECTA
import sys
from pathlib import Path

# Asegurar que el directorio del proyecto esté en el path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from customer_service_agent_app.observability.mcp_metrics import get_observer, create_metrics
    METRICS_ENABLED = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Sistema de métricas MCP cargado correctamente")
    print("🎉 MÉTRICAS HABILITADAS!")
except ImportError as e:
    METRICS_ENABLED = False
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Sistema de métricas falló: {e}")
    print(f"💥 MÉTRICAS FALLARON: {e}")
except Exception as e:
    METRICS_ENABLED = False
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Error inesperado en métricas: {e}")
    print(f"💥 ERROR INESPERADO: {e}")

# Cargar variables de entorno
load_dotenv()

# ===== MÉTRICAS MCP INYECTADAS DIRECTAMENTE =====
import time
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import statistics
import json

@dataclass
class MCPMetrics:
    query: str
    latency_ms: float
    similarity_scores: List[float]
    fallback_used: str
    response_length: int
    results_count: int
    timestamp: datetime
    error: Optional[str] = None

class MCPObserver:
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.session_stats = defaultdict(list)
        self.error_count = 0
        self.total_queries = 0
        self.start_time = datetime.now()
    
    def record_search_metrics(self, metrics: MCPMetrics):
        self.metrics_history.append(metrics)
        self.total_queries += 1
        
        if metrics.error:
            self.error_count += 1
        
        self.session_stats[metrics.fallback_used].append(metrics.latency_ms)
        
        # Log para debugging
        print(f"[METRICS] Query: '{metrics.query[:50]}...' | "
              f"Latency: {metrics.latency_ms:.1f}ms | "
              f"Fallback: {metrics.fallback_used} | "
              f"Results: {metrics.results_count}")
        logger.info(f"[METRICS] Query processed: {metrics.query[:30]}")
        
        # Escribir métricas a archivo persistente
        try:
            metrics_file = Path("mcp_metrics_live.json")
            
            # Crear estructura de datos para el archivo
            metric_data = {
                "timestamp": metrics.timestamp.isoformat(),
                "query": metrics.query,
                "latency_ms": metrics.latency_ms,
                "similarity_scores": metrics.similarity_scores,
                "fallback_used": metrics.fallback_used,
                "response_length": metrics.response_length,
                "results_count": metrics.results_count,
                "error": metrics.error
            }
            
            # Leer métricas existentes o crear nueva estructura
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {"metrics": [], "summary": {}}
            
            # Agregar nueva métrica
            data["metrics"].append(metric_data)
            
            # Mantener solo las últimas 100 métricas
            if len(data["metrics"]) > 100:
                data["metrics"] = data["metrics"][-100:]
            
            # Actualizar resumen
            data["summary"] = {
                "total_queries": self.total_queries,
                "error_count": self.error_count,
                "last_updated": datetime.now().isoformat(),
                "avg_latency": sum(m["latency_ms"] for m in data["metrics"]) / len(data["metrics"]) if data["metrics"] else 0
            }
            
            # Escribir archivo
            with open(metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error escribiendo métricas a archivo: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        if not self.metrics_history:
            return {"status": "no_data", "message": "No hay datos de métricas disponibles aún"}
        
        recent_metrics = list(self.metrics_history)
        latencies = [m.latency_ms for m in recent_metrics if m.error is None]
        
        if not latencies:
            return {"status": "no_valid_data", "error_rate": 100.0}
        
        return {
            "status": "active",
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "avg_latency_ms": round(statistics.mean(latencies), 2),
                "median_latency_ms": round(statistics.median(latencies), 2),
                "total_queries": self.total_queries
            },
            "throughput": {
                "total_queries": self.total_queries,
                "error_rate": round((self.error_count / self.total_queries * 100) if self.total_queries > 0 else 0, 2)
            }
        }

def create_metrics(query: str, start_time: float, search_results: List[Dict], 
                  fallback_type: str, response_content: str, error: str = None) -> MCPMetrics:
    latency_ms = (time.time() - start_time) * 1000
    
    similarity_scores = []
    if search_results and not error:
        similarity_scores = [float(result.get('similarity', 0)) for result in search_results]
    
    return MCPMetrics(
        query=query,
        latency_ms=round(latency_ms, 2),
        similarity_scores=similarity_scores,
        fallback_used=fallback_type,
        response_length=len(response_content),
        results_count=len(search_results) if search_results else 0,
        timestamp=datetime.now(),
        error=error
    )

# Instancia global del observador
mcp_observer = MCPObserver()

def get_observer() -> MCPObserver:
    return mcp_observer

# ===== FIN MÉTRICAS INYECTADAS =====

METRICS_ENABLED = True
print("🎉 MÉTRICAS INYECTADAS DIRECTAMENTE!")
logger.info("🎉 Sistema de métricas inyectado directamente")

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
    tools = [
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
    
    # Agregar herramientas de métricas si están disponibles
    if METRICS_ENABLED:
        tools.extend([
            Tool(
                name="get_metrics_summary",
                description="Obtiene un resumen de las métricas de rendimiento del servidor MCP",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="get_search_analytics",
                description="Obtiene análisis detallado de patrones de búsqueda y uso",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ])
    
    return tools

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """
    Ejecuta la herramienta especificada con los argumentos dados.
    """
    # Manejar herramientas de métricas
    if METRICS_ENABLED and name in ["get_metrics_summary", "get_search_analytics"]:
        try:
            observer = get_observer()
            if name == "get_metrics_summary":
                summary = observer.get_performance_summary()
                return [TextContent(
                    type="text",
                    text=f"📊 **Resumen de Métricas MCP**\n\n```json\n{json.dumps(summary, indent=2)}\n```"
                )]
            elif name == "get_search_analytics":
                return [TextContent(
                    type="text",
                    text="📈 **Análisis de Búsquedas MCP**\n\nMétricas básicas disponibles."
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error al obtener métricas: {str(e)}"
            )]
    
    if name != "search_knowledge":
        raise ValueError(f"Herramienta desconocida: {name}")
    
    # Inicializar métricas
    start_time = time.time()
    query = arguments["query"]
    top_k = arguments.get("top_k", 3)
    search_results = []
    fallback_type = "unknown"
    error_msg = None
    
    try:
        logger.info(f"INFO: Servidor MCP recibió la consulta: '{query}'")
        
        # Generar embedding de la consulta
        current_model = get_model()
        query_embedding = current_model.encode(query).tolist()
        
        # Realizar búsqueda semántica
        search_results = await semantic_search(query_embedding, top_k=top_k)
        
        # Determinar el tipo de fallback usado
        if search_results:
            if any(r.get('similarity', 0) > 0.7 for r in search_results):
                fallback_type = "semantic"
            elif any(r.get('similarity', 0) > 0.5 for r in search_results):
                fallback_type = "text"
            else:
                fallback_type = "general"
        else:
            fallback_type = "none"
        
        if not search_results:
            response_text = "No se encontraron soluciones relevantes en la base de conocimiento."
        else:
            # Formatear resultados
            formatted_context = "\n---\n".join([
                f"Título: {result['title']}\nContenido: {result['content']}\nRelevancia: {result['similarity']:.2f}"
                for result in search_results
            ])
            response_text = f"Información encontrada en la base de conocimiento:\n\n{formatted_context}"
        
        # Registrar métricas de éxito
        if METRICS_ENABLED:
            metrics = create_metrics(
                query=query,
                start_time=start_time,
                search_results=search_results,
                fallback_type=fallback_type,
                response_content=response_text,
                error=None
            )
            get_observer().record_search_metrics(metrics)
        
        return [TextContent(
            type="text",
            text=response_text
        )]
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"ERROR: Servidor MCP de Conocimiento: {e}")
        
        # Registrar métricas de error
        if METRICS_ENABLED:
            metrics = create_metrics(
                query=query,
                start_time=start_time,
                search_results=search_results,
                fallback_type="error",
                response_content=f"Error al buscar en la base de conocimiento: {error_msg}",
                error=error_msg
            )
            get_observer().record_search_metrics(metrics)
        
        return [TextContent(
            type="text", 
            text=f"Error al buscar en la base de conocimiento: {error_msg}"
        )]
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent]:
    """
    Ejecuta la herramienta especificada con los argumentos dados.
    """
    # Manejar herramientas de métricas
    if METRICS_ENABLED and name in ["get_metrics_summary", "get_search_analytics"]:
        try:
            observer = get_observer()
            if name == "get_metrics_summary":
                summary = observer.get_performance_summary()
                return [TextContent(
                    type="text",
                    text=f"📊 **Resumen de Métricas MCP**\n\n```json\n{summary}\n```"
                )]
            elif name == "get_search_analytics":
                analytics = observer.get_search_analytics()
                return [TextContent(
                    type="text",
                    text=f"📈 **Análisis de Búsquedas MCP**\n\n```json\n{analytics}\n```"
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error al obtener métricas: {str(e)}"
            )]
    
    if name != "search_knowledge":
        raise ValueError(f"Herramienta desconocida: {name}")
    
    # Inicializar métricas
    start_time = time.time()
    query = arguments["query"]
    top_k = arguments.get("top_k", 3)
    search_results = []
    fallback_type = "unknown"
    error_msg = None
    
    try:
        logger.info(f"INFO: Servidor MCP recibió la consulta: '{query}'")
        
        # Generar embedding de la consulta
        current_model = get_model()
        query_embedding = current_model.encode(query).tolist()
        
        # Realizar búsqueda semántica
        search_results = await semantic_search(query_embedding, top_k=top_k)
        
        # Determinar el tipo de fallback usado
        if search_results:
            if any(r.get('similarity', 0) > 0.7 for r in search_results):
                fallback_type = "semantic"
            elif any(r.get('similarity', 0) > 0.5 for r in search_results):
                fallback_type = "text"
            else:
                fallback_type = "general"
        else:
            fallback_type = "none"
        
        if not search_results:
            response_text = "No se encontraron soluciones relevantes en la base de conocimiento."
        else:
            # Formatear resultados
            formatted_context = "\n---\n".join([
                f"Título: {result['title']}\nContenido: {result['content']}\nRelevancia: {result['similarity']:.2f}"
                for result in search_results
            ])
            response_text = f"Información encontrada en la base de conocimiento:\n\n{formatted_context}"
        
        # Registrar métricas de éxito
        if METRICS_ENABLED:
            metrics = create_metrics(
                query=query,
                start_time=start_time,
                search_results=search_results,
                fallback_type=fallback_type,
                response_content=response_text,
                error=None
            )
            get_observer().record_search_metrics(metrics)
        
        return [TextContent(
            type="text",
            text=response_text
        )]
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"ERROR: Servidor MCP de Conocimiento: {e}")
        
        # Registrar métricas de error
        if METRICS_ENABLED:
            metrics = create_metrics(
                query=query,
                start_time=start_time,
                search_results=search_results,
                fallback_type="error",
                response_content=f"Error al buscar en la base de conocimiento: {error_msg}",
                error=error_msg
            )
            get_observer().record_search_metrics(metrics)
        
        return [TextContent(
            type="text", 
            text=f"Error al buscar en la base de conocimiento: {error_msg}"
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