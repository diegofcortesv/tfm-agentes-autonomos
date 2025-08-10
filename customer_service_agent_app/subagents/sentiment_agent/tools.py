# customer_service_agent_app/subagents/sentiment_agent/tools.py
from typing import Dict, Any
from customer_service_agent_app.repository.sentiment_repository import SentimentRepository

class SentimentAnalysisTool:
    def __init__(self):
        self.repository = SentimentRepository()
        # Diccionarios de palabras clave para análisis de sentimiento
        self.positive_keywords = [
            "gracias", "excelente", "perfecto", "genial", "satisfecho", 
            "contento", "bien", "bueno", "correcto", "rápido", "eficiente",
            "amable", "servicio excelente", "muy bien", "fantástico"
        ]
        
        self.negative_keywords = [
            "molesto", "enojado", "frustrado", "terrible", "horrible", 
            "malo", "lento", "problema", "error", "falla", "deficiente",
            "pésimo", "inaceptable", "indignado", "furioso", "decepcionado"
        ]
        
        self.urgency_keywords = [
            "urgente", "inmediato", "rápido", "ya", "ahora", "crisis",
            "crítico", "emergencia", "prioritario", "cuanto antes",
            "no puede esperar", "necesito ya"
        ]
        
        self.escalation_keywords = [
            "supervisor", "gerente", "queja", "demanda", "legal",
            "cancelar", "cerrar cuenta", "competencia", "abogado",
            "formal complaint", "escalate", "manager"
        ]
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analiza el sentimiento, primero revisando el caché."""
        if not text:
            return {"error": "No text provided"}

        # Revisar el caché primero
        cached_result = await self.repository.get_from_cache(text)
        if cached_result:
            print("INFO: Sentimiento recuperado del caché.")
            return cached_result

        text_lower = text.lower()
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        urgency_count = sum(1 for word in self.urgency_keywords if word in text_lower)
        escalation_count = sum(1 for word in self.escalation_keywords if word in text_lower)
        
        # Determinar sentimiento principal
        if negative_count > positive_count:
            primary_sentiment = "negative"
        elif positive_count > negative_count:
            primary_sentiment = "positive"
        else:
            primary_sentiment = "neutral"

        # Determinar indicadores adicionales
        urgency_level = "high" if urgency_count > 0 else "normal"
        escalation_risk = "high" if escalation_count > 0 else "low"
        
        # Intensidad emocional
        emotional_intensity = min((positive_count + negative_count) / 5, 1.0)
        
        # Calcular score de confianza
        total_emotional_words = positive_count + negative_count + urgency_count + escalation_count
        confidence = min(total_emotional_words / 8, 1.0)  # Normalizar a 0-1
        
        analysis = {
            "primary_sentiment": primary_sentiment,
            "urgency_level": urgency_level,
            "escalation_risk": escalation_risk,
            "emotional_intensity": emotional_intensity,
            "confidence_score": confidence,
            "detected_keywords": {
                "positive": positive_count,
                "negative": negative_count,
                "urgency": urgency_count,
                "escalation": escalation_count
            },
            "recommended_tone": self._get_recommended_tone(primary_sentiment, urgency_level, escalation_risk)
        
        }

        await self.repository.save_to_cache(text, analysis)
        
        return analysis

    def _get_recommended_tone(self, sentiment: str, urgency: str, escalation_risk: str) -> str:
        """Recommend appropriate response tone"""
        if escalation_risk == "high":
            return "empathetic_professional"
        elif sentiment == "negative" and urgency == "high":
            return "urgent_supportive"
        elif sentiment == "negative":
            return "apologetic_helpful"
        elif urgency == "high":
            return "efficient_direct"
        else:
            return "friendly_professional"