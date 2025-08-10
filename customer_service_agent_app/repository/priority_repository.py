# customer_service_agent_app/repository/priority_repository.py
import asyncpg
from typing import List, Dict, Any
from config.settings import settings

class PriorityRepository:
    def __init__(self):
        self.connection_params = {
            "host": "127.0.0.1",
            "port": settings.PROXY_PORT,
            "database": settings.DB_NAME,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD
        }

    async def get_connection(self):
        return await asyncpg.connect(**self.connection_params)
        
    async def get_active_rules(self) -> List[Dict[str, Any]]:
        """Obtiene las reglas de priorización activas desde la BD."""
        conn = await self.get_connection()
        try:
            # Consulta la tabla que creaste en init_database.py
            rules_records = await conn.fetch("SELECT condition, priority_adjustment FROM priority_rules WHERE active = TRUE;")
            return [dict(rule) for rule in rules_records]
        finally:
            await conn.close()