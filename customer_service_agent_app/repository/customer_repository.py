#!/usr/bin/env python3
"""
Repositorio para gestión de clientes con PostgreSQL
Reemplaza los datos en memoria del CustomerContextTool
"""
import asyncpg
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from config.settings import settings

class CustomerRepository:
    """Repositorio para gestión de datos de clientes en PostgreSQL"""
    
    def __init__(self):
        
        self.connection_params = {
            "host": "127.0.0.1",  # Siempre localhost para el proxy
            "port": settings.PROXY_PORT,
            "database": settings.DB_NAME,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD
        }
       
    async def get_connection(self):
        """Obtener conexión a la base de datos"""
        return await asyncpg.connect(**self.connection_params)
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Obtener cliente por ID desde PostgreSQL"""
        conn = await self.get_connection()
        
        try:
            # Consultar datos básicos del cliente
            customer_row = await conn.fetchrow("""
                SELECT customer_id, name, tier, join_date, satisfaction_score, 
                       total_interactions, preferred_channel, language,
                       created_at, updated_at
                FROM customer_profiles 
                WHERE customer_id = $1
            """, customer_id)
            
            if not customer_row:
                return None
            
            # Convertir a diccionario
            customer_data = dict(customer_row)
            
            # Obtener interacciones recientes
            recent_interactions = await conn.fetch("""
                SELECT issue_type, sentiment, priority_level, created_at
                FROM customer_interactions 
                WHERE customer_id = $1 
                ORDER BY created_at DESC 
                LIMIT 5
            """, customer_id)
            
            # Extraer tipos de issues recientes
            recent_issues = [interaction['issue_type'] for interaction in recent_interactions if interaction['issue_type']]
            
            # Formatear datos para compatibilidad con herramienta original
            formatted_customer = {
                "customer_id": customer_data["customer_id"],
                "name": customer_data["name"],
                "tier": customer_data["tier"],
                "join_date": customer_data["join_date"].strftime("%Y-%m-%d") if customer_data["join_date"] else None,
                "total_interactions": customer_data["total_interactions"],
                "recent_issues": recent_issues,
                "satisfaction_score": customer_data["satisfaction_score"],
                "last_interaction": recent_interactions[0]['created_at'].strftime("%Y-%m-%d") if recent_interactions else None,
                "preferred_channel": customer_data["preferred_channel"],
                "language": customer_data["language"]
            }
            
            return formatted_customer
            
        finally:
            await conn.close()
    
    async def get_customer_context(self, customer_id: str) -> Dict[str, Any]:
        """
        Obtener contexto completo del cliente (compatible con tool original)
        """
        customer_data = await self.get_customer_by_id(customer_id)
        
        if not customer_data:
            return {
                "error": f"Customer {customer_id} not found",
                "customer_id": customer_id,
                "suggestion": "Please verify customer ID or ask customer to provide correct identification"
            }
        
        # Calcular métricas adicionales
        try:
            if customer_data["last_interaction"]:
                last_interaction_date = datetime.strptime(customer_data["last_interaction"], "%Y-%m-%d")
                days_since_last = (datetime.now() - last_interaction_date).days
            else:
                days_since_last = 0
        except:
            days_since_last = 0
        
        is_frequent_user = customer_data["total_interactions"] > 5
        is_vip = customer_data["tier"] in ["Premium", "Gold"]
        risk_level = "high" if customer_data["satisfaction_score"] < 3.5 else "low"
        
        return {
            "customer_id": customer_id,
            "customer_data": customer_data,
            "calculated_metrics": {
                "days_since_last_interaction": days_since_last,
                "is_frequent_user": is_frequent_user,
                "is_vip_customer": is_vip,
                "risk_level": risk_level,
                "tier_priority": {"Premium": 3, "Gold": 2, "Basic": 1}.get(customer_data["tier"], 1)
            }
        }
    
    async def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> bool:
        """Actualizar datos de cliente"""
        conn = await self.get_connection()
        
        try:
            # Construir query dinámico basado en campos a actualizar
            set_clauses = []
            values = []
            param_count = 1
            
            for field, value in updates.items():
                if field in ['satisfaction_score', 'total_interactions', 'preferred_channel', 'tier']:
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(value)
                    param_count += 1
            
            if not set_clauses:
                return False
            
            # Añadir updated_at
            set_clauses.append(f"updated_at = ${param_count}")
            values.append(datetime.now())
            values.append(customer_id)  # Para el WHERE
            
            query = f"""
                UPDATE customer_profiles 
                SET {', '.join(set_clauses)}
                WHERE customer_id = ${param_count + 1}
            """
            
            result = await conn.execute(query, *values)
            return result == "UPDATE 1"
            
        finally:
            await conn.close()
    
    async def add_interaction(self, customer_id: str, interaction_data: Dict[str, Any]) -> bool:
        """Registrar nueva interacción"""
        conn = await self.get_connection()
        
        try:
            # Insertar interacción
            await conn.execute("""
                INSERT INTO customer_interactions 
                (customer_id, interaction_type, issue_type, message, sentiment, priority_level, agent_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                customer_id,
                interaction_data.get("interaction_type", "chat"),
                interaction_data.get("issue_type"),
                interaction_data.get("message"),
                interaction_data.get("sentiment"),
                interaction_data.get("priority_level"),
                interaction_data.get("agent_id", "context_analyzer")
            )
            
            # Actualizar contador de interacciones del cliente
            await conn.execute("""
                UPDATE customer_profiles 
                SET total_interactions = total_interactions + 1,
                    updated_at = NOW()
                WHERE customer_id = $1
            """, customer_id)
            
            return True
            
        except Exception as e:
            print(f"Error adding interaction: {e}")
            return False
        finally:
            await conn.close()
    
    async def get_customer_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas generales de clientes"""
        conn = await self.get_connection()
        
        try:
            stats = {}
            
            # Conteo por tier
            tier_stats = await conn.fetch("""
                SELECT tier, COUNT(*) as count 
                FROM customer_profiles 
                GROUP BY tier
            """)
            stats["by_tier"] = {row["tier"]: row["count"] for row in tier_stats}
            
            # Total de clientes
            total_customers = await conn.fetchval("SELECT COUNT(*) FROM customer_profiles")
            stats["total_customers"] = total_customers
            
            # Promedio de satisfacción
            avg_satisfaction = await conn.fetchval("SELECT AVG(satisfaction_score) FROM customer_profiles")
            stats["average_satisfaction"] = round(float(avg_satisfaction), 2) if avg_satisfaction else 0.0
            
            # Clientes de alto riesgo
            high_risk = await conn.fetchval("""
                SELECT COUNT(*) FROM customer_profiles 
                WHERE satisfaction_score < 3.5
            """)
            stats["high_risk_customers"] = high_risk
            
            return stats
            
        finally:
            await conn.close()
    
    async def update_customer_metric(self, customer_id: str, field: str, value: Any) -> bool:
        """Actualiza una métrica específica de un cliente."""
        conn = await self.get_connection()
        try:
            # Esta validación evita la inyección de SQL en los nombres de columna
            if field not in ['satisfaction_score', 'total_interactions', 'preferred_channel', 'tier']:
                raise ValueError(f"Campo no válido para actualizar: {field}")

            query = f"""
                UPDATE customer_profiles 
                SET {field} = $1, updated_at = NOW()
                WHERE customer_id = $2
            """
            result = await conn.execute(query, value, customer_id)
            # asyncpg devuelve un string como 'UPDATE 1', lo comprobamos
            return "UPDATE 1" in str(result)
        finally:
            await conn.close()

# Función para testing
async def test_customer_repository():
    """Función de test para verificar que el repositorio funciona"""
    repo = CustomerRepository()
    
    print("🧪 Probando Customer Repository...")
    
    # Test 1: Obtener cliente existente
    context = await repo.get_customer_context("CUST_001")
    if "error" not in context:
        print(f"✅ Cliente encontrado: {context['customer_data']['name']}")
        print(f"   Tier: {context['customer_data']['tier']}")
        print(f"   Interacciones: {context['customer_data']['total_interactions']}")
        print(f"   VIP: {context['calculated_metrics']['is_vip_customer']}")
    else:
        print("❌ Error obteniendo cliente")
    
    # Test 2: Cliente no existente
    context_missing = await repo.get_customer_context("CUST_999")
    if "error" in context_missing:
        print(" Cliente inexistente manejado correctamente")
    
    # Test 3: Estadísticas
    stats = await repo.get_customer_statistics()
    print(f"   Estadísticas: {stats['total_customers']} clientes totales")
    print(f"   Por tier: {stats['by_tier']}")
    print(f"   Satisfacción promedio: {stats['average_satisfaction']}")
    
    print(" Customer Repository funcionando correctamente!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_customer_repository())

    async def update_customer_metric(self, customer_id: str, field: str, value: Any) -> bool:
        """Actualiza una métrica específica de un cliente."""
        conn = await self.get_connection()
        try:
            # Esta es una forma segura de construir la consulta para evitar inyección SQL
            # ya que el nombre del campo está validado.
            if field not in ['satisfaction_score', 'total_interactions', 'preferred_channel', 'tier']:
                raise ValueError("Campo no válido para actualizar.")

            query = f"""
                UPDATE customer_profiles 
                SET {field} = $1, updated_at = NOW()
                WHERE customer_id = $2
            """
            result = await conn.execute(query, value, customer_id)
            return "UPDATE 1" in result
        finally:
            await conn.close()

