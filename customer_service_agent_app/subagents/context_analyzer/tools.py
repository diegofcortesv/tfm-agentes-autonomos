import re
from typing import Dict, Any
import asyncio

from customer_service_agent_app.repository.customer_repository import CustomerRepository

class CustomerContextToolV2:
    """Tool actualizada para análisis de contexto usando PostgreSQL"""
    
    def __init__(self):
        self.repository = CustomerRepository()
    
    async def get_customer_context(self, customer_message: str) -> Dict[str, Any]:
        """
        Extraer ID del cliente del mensaje y obtener contexto desde BD
        Compatible con la interfaz original de la tool
        """
        # Extraer customer ID del mensaje
        customer_id = self._extract_customer_id(customer_message)
        
        if not customer_id:
            return {
                "error": "No se encontró ID de cliente en el mensaje",
                "message": customer_message,
                "suggestion": "Por favor solicite al cliente que proporcione su ID de cliente (formato: CUST_XXX)"
            }
        
        # Obtener contexto desde base de datos (función asíncrona)
        # Necesitamos usar asyncio para ejecutar la función asíncrona
        try:
            # Llama directamente a la función asíncrona usando await
            context = await self.repository.get_customer_context(customer_id)
            return context
        except Exception as e:
            return {
                "error": f"Error accediendo a base de datos: {str(e)}",
                "customer_id": customer_id,
                "suggestion": "Verifique la conexión a la base de datos"
            }
    
    def _extract_customer_id(self, message: str) -> str:
        """Extraer customer ID del mensaje del cliente"""
        # Buscar patrones como "CUST_001", "cliente CUST_002", etc.
        patterns = [
            r'CUST_\d{3}',  # CUST_001
            r'customer\s+CUST_\d{3}',  # customer CUST_001
            r'cliente\s+CUST_\d{3}',   # cliente CUST_001
            r'ID:\s*CUST_\d{3}',       # ID: CUST_001
            r'soy\s+CUST_\d{3}',       # soy CUST_001
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Extraer solo la parte CUST_XXX
                customer_id_match = re.search(r'CUST_\d{3}', match.group())
                if customer_id_match:
                    return customer_id_match.group()
        
        return None
    
    async def add_interaction_async(self, customer_id: str, interaction_data: Dict[str, Any]) -> bool:
        """Registrar interacción de forma asíncrona"""
        return await self.repository.add_interaction(customer_id, interaction_data)
    
    async def log_interaction_summary(self, customer_id: str, issue_type: str, sentiment: str, resolution_summary: str) -> Dict[str, Any]:
        """
        Registra un resumen de la interacción en la base de datos y actualiza el perfil del cliente.
        """
        print(f"INFO: Registrando interacción para {customer_id}...")
        
        interaction_data = {
            "interaction_type": "chat",
            "issue_type": issue_type,
            "message": resolution_summary,
            "sentiment": sentiment,
            "agent_id": "root_agent"
        }
        
        success = await self.repository.add_interaction(customer_id, interaction_data)
        
        if not success:
            return {"status": "failed", "error": "No se pudo registrar la interacción."}

        # Opcional: Actualizar la puntuación de satisfacción basada en el sentimiento final
        if sentiment == 'positive':
            # Simulación: una interacción positiva aumenta ligeramente la satisfacción
            # En un caso real, esto vendría de una encuesta post-chat
            current_context = await self.repository.get_customer_context(customer_id)
            current_score = current_context['customer_data'].get('satisfaction_score', 3.0)
            new_score = min(5.0, current_score + 0.1) # Aumenta 0.1, con un máximo de 5
            await self.repository.update_customer_metric(customer_id, 'satisfaction_score', new_score)
        
        print(f"✅ Interacción para {customer_id} registrada exitosamente.")
        return {"status": "success", "message": f"Interacción para {customer_id} registrada."}