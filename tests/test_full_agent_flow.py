# tests/test_full_agent_flow.py
import asyncio
import sys
import os
import json

# Añadimos la ruta raíz del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importamos los componentes necesarios
from customer_service_agent_app import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

async def run_full_test():
    """
    Ejecuta un flujo completo a través del root_agent para probar la integración
    de todos los subagentes.
    """
    print("🚀 === INICIANDO PRUEBA DE FLUJO COMPLETO DEL AGENTE RAÍZ === 🚀")

    customer_message = "Hola, soy el cliente CUST_001. Mi servicio no funciona y estoy muy molesto. ¡Necesito ayuda urgente o hablaré con un supervisor!"

    print(f"\n💬 Mensaje del Cliente:\n   '{customer_message}'")
    print("\n🔄 Procesando a través del root_agent...")

    # 1. Creamos un servicio de sesión en memoria
    session_service = InMemorySessionService()

    # 2. Inicializamos el Runner con los argumentos requeridos
    agent_runner = Runner(
        agent=root_agent,
        app_name="CustomerServiceTestRunner",
        session_service=session_service
    )

    # ¡¡¡CAMBIO FINAL!!!
    # 3. Se llama a .run() pasando los argumentos de entrada directamente, no dentro de un diccionario 'input'.
    final_result = await agent_runner.run(customer_message=customer_message)

    print("\n🎉 === PROCESO COMPLETADO === 🎉")

    print("\n📝 Resultados Intermedios de los Agentes Paralelos:")
    
    parallel_results = final_result.get('ParallelCustomerAnalyzer', {})
    
    for agent_name, result in parallel_results.items():
        print(f"\n--- Resultado de {agent_name} ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n--- Resultado del ResponseSynthesizer ---")
    synthesized_response = final_result.get('synthesized_response', {})
    print(json.dumps(synthesized_response, indent=2, ensure_ascii=False))

    print("\n\n✅ ¡La prueba de integración se completó exitosamente!")


if __name__ == "__main__":
    asyncio.run(run_full_test())