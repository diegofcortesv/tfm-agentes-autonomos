# tests/test_context_analyzer.py
import asyncio
from customer_service_agent_app.subagents.context_analyzer.tools import CustomerContextToolV2

# Función de testing para el agent actualizado
async def test_context_analyzer():  # Renombrado para más claridad
    """Test del Context Analyzer Agent V2"""
    print("Probando Context Analyzer Agent V2...")
    
    # Crear una instancia de la herramienta para probarla
    context_tool_v2 = CustomerContextToolV2()

    test_messages = [
        "Hola, soy el cliente CUST_001 y tengo un problema con mi facturación",
        "Buenos días, mi ID es CUST_002 y necesito ayuda técnica",
        "Soy CUST_003, quiero consultar información de mi cuenta",
        "Hola, no tengo mi ID a mano pero necesito ayuda"  # Sin ID
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\nTest {i}: {message[:50]}...")
        result = await context_tool_v2.get_customer_context(message)
        
        if "error" in result:
            print(f"   {result['error']}")
        else:
            customer_data = result.get("customer_data", {})
            metrics = result.get("calculated_metrics", {})
            print(f"      Cliente: {customer_data.get('name', 'N/A')}")
            print(f"      Tier: {customer_data.get('tier', 'N/A')}")
            print(f"      VIP: {metrics.get('is_vip_customer', False)}")
            print(f"      Riesgo: {metrics.get('risk_level', 'unknown')}")

# Script principal para testing
if __name__ == "__main__":
    print("=== Context Analyzer Agent V2 - Test de Herramienta ===")
    asyncio.run(test_context_analyzer())