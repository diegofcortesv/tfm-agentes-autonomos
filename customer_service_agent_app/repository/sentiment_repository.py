# customer_service_agent_app/repository/sentiment_repository.py
import asyncpg
import hashlib
from typing import Optional, Dict, Any
from config.settings import settings

class SentimentRepository:
    def __init__(self):
        self.connection_params = {
            "host": "127.0.0.1", "port": settings.PROXY_PORT,
            "database": settings.DB_NAME, "user": settings.DB_USER,
            "password": settings.DB_PASSWORD
        }

    async def get_connection(self):
        return await asyncpg.connect(**self.connection_params)

    def _hash_message(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    async def get_from_cache(self, text: str) -> Optional[Dict[str, Any]]:
        message_hash = self._hash_message(text)
        conn = await self.get_connection()
        try:
            cached = await conn.fetchrow("SELECT * FROM sentiment_cache WHERE message_hash = $1", message_hash)
            return dict(cached) if cached else None
        finally:
            await conn.close()

    async def save_to_cache(self, text: str, analysis: Dict[str, Any]):
        message_hash = self._hash_message(text)
        conn = await self.get_connection()
        try:
            await conn.execute("""
                INSERT INTO sentiment_cache (message_hash, primary_sentiment, urgency_level, escalation_risk, recommended_tone)
                VALUES ($1, $2, $3, $4, $5) ON CONFLICT (message_hash) DO NOTHING
            """, message_hash, analysis['primary_sentiment'], analysis['urgency_level'], analysis['escalation_risk'], analysis['recommended_tone'])
        finally:
            await conn.close()