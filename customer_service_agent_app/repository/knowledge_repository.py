# customer_service_agent_app/repository/knowledge_repository.py
import asyncpg
from typing import List, Dict, Any
from config.settings import settings
from pgvector.asyncpg import register_vector

class KnowledgeRepository:
    def __init__(self):
        self.connection_params = {
            "host": "127.0.0.1",
            "port": settings.PROXY_PORT,
            "database": settings.DB_NAME,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD
        }

    async def get_connection(self):
        """Obtiene una conexión a la BD y la prepara para pgvector."""
        conn = await asyncpg.connect(**self.connection_params)
        
        # ¡CAMBIO CLAVE! Esta es la función oficial de la librería pgvector
        # para registrar el tipo 'vector' en la conexión activa.
        await register_vector(conn)
        
        return conn
    
    async def semantic_search(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Realiza una búsqueda por similitud de coseno en la knowledge_base."""
        conn = await self.get_connection()
        try:
            # La sintaxis de la consulta es correcta. El problema estaba en la conexión.
            # pgvector usa el operador <=> para la distancia coseno. 1 - distancia = similitud.
            query = """
                SELECT title, content, 1 - (embedding <=> $1) AS similarity
                FROM knowledge_base
                ORDER BY similarity DESC
                LIMIT $2
            """
            # Pasamos la lista de Python directamente. pgvector y asyncpg se encargarán de la conversión.
            results = await conn.fetch(query, query_embedding, top_k)
            return [dict(row) for row in results]
        finally:
            await conn.close()