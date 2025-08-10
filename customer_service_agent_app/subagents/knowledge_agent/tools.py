# customer_service_agent_app/subagents/knowledge_agent/tools.py
from typing import Dict, Any
from sentence_transformers import SentenceTransformer
from customer_service_agent_app.repository.knowledge_repository import KnowledgeRepository

class KnowledgeBaseTool:
    def __init__(self):
        self.repository = KnowledgeRepository()
        # Carga el modelo una vez al iniciar la herramienta.
        print("INFO: Cargando modelo de embeddings para Knowledge Agent...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("INFO: Modelo de embeddings cargado.")
    
    async def search_knowledge_base(self, customer_query: str, issue_type: str = "") -> Dict[str, Any]:
        """Busca en la base de conocimientos usando búsqueda semántica."""
        if not customer_query:
            return {"error": "No query provided"}

        print(f"INFO: Realizando búsqueda semántica para: '{customer_query}'")
        query_embedding = self.model.encode(customer_query).tolist()
        
        search_results = await self.repository.semantic_search(query_embedding, top_k=3)
        
        if not search_results:
            return {
                "found": False,
                "message": "No se encontraron soluciones relevantes en la base de conocimientos.",
            }

        return {
            "found": True,
            "solutions": search_results
        }