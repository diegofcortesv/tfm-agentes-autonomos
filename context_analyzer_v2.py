#!/usr/bin/env python3
"""
Context Analyzer Agent V2 - Versión con base de datos PostgreSQL
Migrado desde herramientas en memoria a repositorio PostgreSQL
"""
from google.adk.agents import LlmAgent
from typing import Dict, Any
import asyncio
import re

# Importar el repositorio de clientes
from customer_repository import CustomerRepository

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

# Crear instancia de la tool actualizada
context_tool_v2 = CustomerContextToolV2()

# Agent actualizado que usa PostgreSQL
context_analyzer_agent_v2 = LlmAgent(
    name="ContextAnalyzerV2",
    model="gemini-2.0-flash",
    description="Analyzes customer context using PostgreSQL database instead of in-memory data",
    instruction="""You are a Context Analysis specialist for customer service, now powered by PostgreSQL database.

Your primary role is to extract customer identification and retrieve their complete profile from the database.

STEP 1: Extract Customer ID
- Look for patterns like "CUST_001", "cliente CUST_002", "customer CUST_003", "soy CUST_001" in the user message
- Customer IDs follow the format CUST_XXX where XXX is a 3-digit number
- If no customer ID is found, ask the customer to provide their customer ID

STEP 2: Retrieve Customer Data from PostgreSQL
- Use the get_customer_context tool with the complete customer message
- The tool will extract the customer ID and query the PostgreSQL database
- Analyze the returned customer profile data

STEP 3: Provide Enhanced Context Analysis
When you have customer data from the database, provide insights about:

**Customer Profile:**
- Customer tier and value assessment (Premium/Gold/Basic)
- Join date and customer lifetime
- Total interactions and engagement level
- Preferred communication channel

**Behavioral Patterns:**
- Recent issue types and trends
- Historical interaction frequency
- Satisfaction score and risk assessment
- VIP status and tier priority

**Risk Assessment:**
- Satisfaction score analysis (risk level: high if < 3.5)
- Days since last interaction
- Escalation patterns from recent issues

**Personalization Recommendations:**
- Communication preferences based on tier and history
- Appropriate tone and approach
- Special handling requirements for VIP customers
- Historical context for better service

**Database-Enhanced Features:**
Your analysis now includes real-time data from PostgreSQL:
- Live customer satisfaction scores
- Complete interaction history
- Dynamic tier-based prioritization
- Risk assessment based on actual data

Format your response clearly with customer insights that other agents can use for personalization and context-aware service.

If there are database connectivity issues, provide helpful troubleshooting guidance.""",
    
    tools=[context_tool_v2.get_customer_context],
    output_key="context_analysis"
)

# Función de testing para el agent actualizado
async def test_context_analyzer_v2():
    """Test del Context Analyzer Agent V2"""
    print("🧪 Probando Context Analyzer Agent V2...")
    
    # Test con mensaje que incluye customer ID
    test_messages = [
        "Hola, soy el cliente CUST_001 y tengo un problema con mi facturación",
        "Buenos días, mi ID es CUST_002 y necesito ayuda técnica",
        "Soy CUST_003, quiero consultar información de mi cuenta",
        "Hola, no tengo mi ID a mano pero necesito ayuda"  # Sin ID
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\nTest {i}: {message[:50]}...")
        
        # Simular el procesamiento del agent
        result = await context_tool_v2.get_customer_context(message)
        
        if "error" in result:
            print(f"   ❌ {result['error']}")
        else:
            customer_data = result.get("customer_data", {})
            metrics = result.get("calculated_metrics", {})
            print(f"   ✅ Cliente: {customer_data.get('name', 'N/A')}")
            print(f"      Tier: {customer_data.get('tier', 'N/A')}")
            print(f"      VIP: {metrics.get('is_vip_customer', False)}")
            print(f"      Riesgo: {metrics.get('risk_level', 'unknown')}")

# Script principal para testing
if __name__ == "__main__":
    print("=== Context Analyzer Agent V2 - PostgreSQL Version ===")
    asyncio.run(test_context_analyzer_v2())