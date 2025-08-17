# customer_service_agent_app/subagents/knowledge_agent/agent.py
from google.adk.agents import LlmAgent
from .tools import knowledge_search_toolset

knowledge_agent = LlmAgent(
    name="KnowledgeSearcher",
    model="gemini-2.0-flash",
    description="Searches knowledge base for relevant solutions and procedures using semantic search.",
    instruction="""You are a Knowledge Base specialist.
    Your role is to find relevant information to solve a customer's problem.
    
    To do this, use the `search_knowledge` tool with the following parameters:
    - query: The customer's question or problem description
    - top_k: Number of results to return (optional, default is 3)
    
    Always search for information that could help resolve the customer's specific issue.
    Return the most relevant knowledge base content that can assist with their problem.""",
    
    tools=[knowledge_search_toolset],
    output_key="knowledge_search"
)