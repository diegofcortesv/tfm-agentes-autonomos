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
        
        await register_vector(conn)
        
        return conn
    
    async def semantic_search(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Realiza una búsqueda por similitud de coseno en la knowledge_base."""
        conn = await self.get_connection()
        try:

            query = """
                SELECT title, content, 1 - (embedding <=> $1) AS similarity
                FROM knowledge_base
                ORDER BY similarity DESC
                LIMIT $2
            """

            results = await conn.fetch(query, query_embedding, top_k)
            return [dict(row) for row in results]
        finally:
            await conn.close()