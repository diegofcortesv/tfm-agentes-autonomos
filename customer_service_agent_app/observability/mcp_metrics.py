# customer_service_agent_app/observability/mcp_metrics.py
import time
import asyncio
import json
from functools import wraps
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict, deque
import statistics

@dataclass
class MCPMetrics:
    """Métricas de una consulta individual al servidor MCP"""
    query: str
    latency_ms: float
    similarity_scores: List[float]
    fallback_used: str  # "semantic", "text", "general"
    response_length: int
    results_count: int
    timestamp: datetime
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class MCPObserver:
    """Observador no invasivo para métricas del servidor MCP"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.session_stats = defaultdict(list)
        self.error_count = 0
        self.total_queries = 0
        self.start_time = datetime.now()
    
    def record_search_metrics(self, metrics: MCPMetrics):
        """Registra métricas de búsqueda sin interferir con el flujo"""
        self.metrics_history.append(metrics)
        self.total_queries += 1
        
        if metrics.error:
            self.error_count += 1
        
        # Agregar a estadísticas de sesión por tipo de fallback
        self.session_stats[metrics.fallback_used].append(metrics.latency_ms)
        
        # Log para debugging (opcional)
        print(f"[METRICS] Query: '{metrics.query[:50]}...' | "
              f"Latency: {metrics.latency_ms:.1f}ms | "
              f"Fallback: {metrics.fallback_used} | "
              f"Results: {metrics.results_count}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Genera resumen de rendimiento para dashboard"""
        if not self.metrics_history:
            return {
                "status": "no_data",
                "message": "No hay datos de métricas disponibles aún"
            }
        
        # Convertir a lista para facilitar cálculos
        recent_metrics = list(self.metrics_history)
        
        # Métricas de latencia
        latencies = [m.latency_ms for m in recent_metrics if m.error is None]
        
        if not latencies:
            return {"status": "no_valid_data", "error_rate": 100.0}
        
        # Estadísticas de latencia
        avg_latency = statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        p95_latency = self._percentile(latencies, 95)
        
        # Análisis de fallback
        fallback_counts = defaultdict(int)
        for m in recent_metrics:
            fallback_counts[m.fallback_used] += 1
        
        total_valid = len([m for m in recent_metrics if m.error is None])
        fallback_rates = {
            fb_type: (count / total_valid * 100) if total_valid > 0 else 0
            for fb_type, count in fallback_counts.items()
        }
        
        # Análisis de calidad de resultados
        similarity_scores = []
        for m in recent_metrics:
            if m.similarity_scores and m.error is None:
                similarity_scores.extend(m.similarity_scores)
        
        avg_similarity = statistics.mean(similarity_scores) if similarity_scores else 0.0
        
        # Métricas de throughput
        uptime_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        queries_per_minute = self.total_queries / uptime_minutes if uptime_minutes > 0 else 0
        
        return {
            "status": "active",
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "avg_latency_ms": round(avg_latency, 2),
                "median_latency_ms": round(median_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "min_latency_ms": round(min(latencies), 2),
                "max_latency_ms": round(max(latencies), 2)
            },
            "quality": {
                "avg_similarity_score": round(avg_similarity, 3),
                "semantic_success_rate": fallback_rates.get("semantic", 0),
                "fallback_rates": fallback_rates
            },
            "throughput": {
                "total_queries": self.total_queries,
                "queries_per_minute": round(queries_per_minute, 2),
                "error_rate": round((self.error_count / self.total_queries * 100) if self.total_queries > 0 else 0, 2),
                "uptime_minutes": round(uptime_minutes, 2)
            },
            "recent_activity": {
                "last_query_time": recent_metrics[-1].timestamp.isoformat() if recent_metrics else None,
                "recent_queries_count": len(recent_metrics),
                "window_size": self.max_history
            }
        }
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """Análisis detallado de patrones de búsqueda"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        recent_metrics = list(self.metrics_history)
        
        # Análisis de patrones de consulta
        query_lengths = [len(m.query) for m in recent_metrics]
        response_lengths = [m.response_length for m in recent_metrics if m.error is None]
        
        # Top consultas por tipo de fallback
        fallback_patterns = defaultdict(list)
        for m in recent_metrics:
            fallback_patterns[m.fallback_used].append({
                "query": m.query[:100],  # Truncar para privacidad
                "latency": m.latency_ms,
                "similarity": max(m.similarity_scores) if m.similarity_scores else 0
            })
        
        return {
            "query_patterns": {
                "avg_query_length": round(statistics.mean(query_lengths), 1) if query_lengths else 0,
                "avg_response_length": round(statistics.mean(response_lengths), 1) if response_lengths else 0,
                "most_common_fallback": max(fallback_patterns.keys(), 
                                          key=lambda k: len(fallback_patterns[k])) if fallback_patterns else None
            },
            "fallback_analysis": {
                fb_type: {
                    "count": len(queries),
                    "avg_latency": round(statistics.mean([q["latency"] for q in queries]), 2) if queries else 0,
                    "avg_similarity": round(statistics.mean([q["similarity"] for q in queries if q["similarity"] > 0]), 3) if queries else 0
                }
                for fb_type, queries in fallback_patterns.items()
            }
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcula percentil de una lista de datos"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (percentile / 100)
        f = int(k)
        c = k - f
        if f + 1 < len(sorted_data):
            return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
        return sorted_data[f]
    
    def export_metrics(self, format: str = "json") -> str:
        """Exporta métricas para análisis externo"""
        if format == "json":
            metrics_data = [m.to_dict() for m in self.metrics_history]
            return json.dumps({
                "metrics": metrics_data,
                "summary": self.get_performance_summary(),
                "exported_at": datetime.now().isoformat()
            }, indent=2)
        else:
            raise ValueError(f"Formato no soportado: {format}")
    
    def reset_metrics(self):
        """Reinicia las métricas (útil para testing)"""
        self.metrics_history.clear()
        self.session_stats.clear()
        self.error_count = 0
        self.total_queries = 0
        self.start_time = datetime.now()
        print("[METRICS] Métricas reiniciadas")

# Instancia global del observador
mcp_observer = MCPObserver()

def get_observer() -> MCPObserver:
    """Obtiene la instancia global del observador"""
    return mcp_observer

# Función de utilidad para crear métricas fácilmente
def create_metrics(query: str, start_time: float, search_results: List[Dict], 
                  fallback_type: str, response_content: str, error: str = None) -> MCPMetrics:
    """Factory function para crear métricas de forma consistente"""
    latency_ms = (time.time() - start_time) * 1000
    
    similarity_scores = []
    if search_results and not error:
        similarity_scores = [float(result.get('similarity', 0)) for result in search_results]
    
    return MCPMetrics(
        query=query,
        latency_ms=round(latency_ms, 2),
        similarity_scores=similarity_scores,
        fallback_used=fallback_type,
        response_length=len(response_content),
        results_count=len(search_results) if search_results else 0,
        timestamp=datetime.now(),
        error=error
    )