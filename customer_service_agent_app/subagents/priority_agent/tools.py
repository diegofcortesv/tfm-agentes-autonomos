# customer_service_agent_app/subagents/priority_agent/tools.py
from typing import Dict, Any
#  Importamos el repositorio
from customer_service_agent_app.repository.priority_repository import PriorityRepository

class PriorityAssessmentTool:
    def __init__(self):
        # Instanciamos el repositorio
        self.repository = PriorityRepository()
    
    async def calculate_priority(self, customer_tier: str, issue_type: str, sentiment: str, urgency: str, escalation_risk: str) -> Dict[str, Any]:
        """Calcula la prioridad basándose en factores y reglas de la BD."""
        
        priority_score = 0
        factors = []
                
        tier_weights = {"Premium": 4, "Gold": 3, "Basic": 1}
        tier_score = tier_weights.get(customer_tier, 1)
        priority_score += tier_score
        factors.append(f"Customer tier ({customer_tier}): +{tier_score}")
        
        # Factor: Issue Type
        issue_weights = {"técnico": 3, "facturación": 2, "general": 1}
        issue_score = issue_weights.get(issue_type.lower(), 1)
        priority_score += issue_score
        factors.append(f"Issue type ({issue_type}): +{issue_score}")
        
        # Factor: Sentiment (peso medio)
        sentiment_weights = {"negative": 3, "neutral": 1, "positive": 0}
        sentiment_score = sentiment_weights.get(sentiment.lower(), 1)
        priority_score += sentiment_score
        factors.append(f"Sentiment ({sentiment}): +{sentiment_score}")
        
        # Factor: Urgency (peso alto)
        urgency_score = 4 if urgency.lower() == "high" else 0
        priority_score += urgency_score
        if urgency_score > 0:
            factors.append(f"High urgency: +{urgency_score}")
        
        # Factor: Escalation Risk (peso alto)
        escalation_score = 3 if escalation_risk.lower() == "high" else 0
        priority_score += escalation_score
        if escalation_score > 0:
            factors.append(f"Escalation risk: +{escalation_score}")
        
        # Determinar nivel de prioridad y routing
        if priority_score >= 10:
            priority_level = "Critical"
            sla_target = "5 minutes"
            routing = "Senior Agent + Supervisor Notification"
            queue_position = 1
        elif priority_score >= 7:
            priority_level = "High"
            sla_target = "15 minutes"
            routing = "Experienced Agent"
            queue_position = 2
        elif priority_score >= 4:
            priority_level = "Medium"
            sla_target = "1 hour"
            routing = "Standard Agent"
            queue_position = 3
        else:
            priority_level = "Low"
            sla_target = "4 hours"
            routing = "Any Available Agent"
            queue_position = 4
        
        # Determinar acciones adicionales
        requires_supervisor = priority_level in ["Critical", "High"] and escalation_risk == "high"
        requires_followup = priority_level in ["Critical", "High"] or escalation_risk == "high"
        
        return {
            "priority_score": priority_score,
            "priority_level": priority_level,
            "sla_target": sla_target,
            "recommended_routing": routing,
            "queue_position": queue_position,
            "scoring_factors": factors,
            "requires_supervisor": requires_supervisor,
            "requires_followup": requires_followup,
            "max_possible_score": 15,  # Para contexto
            "priority_percentage": round((priority_score / 15) * 100, 1)
        }