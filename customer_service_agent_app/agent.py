# customer_service_agent_app/agent.py

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

# Importar todos los sub-agentes
from google.adk.agents import ParallelAgent, SequentialAgent
from .subagents.context_analyzer.agent import context_analyzer_agent_v2 as context_analyzer_agent
from .subagents.sentiment_agent.agent import sentiment_agent
from .subagents.knowledge_agent.agent import knowledge_agent
from .subagents.priority_agent.agent import priority_agent
from .subagents.response_synthesizer.agent import response_synthesizer

# Agente paralelo para análisis simultáneo
parallel_analyzer = ParallelAgent(
    name="ParallelCustomerAnalyzer",
    description="Concurrently analyzes customer context, sentiment, knowledge base, and priority to provide comprehensive customer insights",
    sub_agents=[
        context_analyzer_agent,
        sentiment_agent,
        knowledge_agent,
        priority_agent
    ]
)

# Agente raíz que combina análisis paralelo + síntesis secuencial
root_agent = SequentialAgent(
    name="CustomerServiceAgent",
    description="Autonomous customer service agent with parallel analysis and response synthesis. Provides personalized, contextual, and solution-focused customer service using specialized AI agents.",
    sub_agents=[
        parallel_analyzer,
        response_synthesizer
    ]
)

print("Customer Service Agent System Loaded Successfully!")
print(f"Root Agent: {root_agent.name}")