# scripts/init_database.py
import asyncio
import asyncpg
from datetime import datetime
import sys
import os

# Añade la ruta raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import settings

async def init_database():
    """Inicializar base de datos con todas las tablas"""
    
    print("🏗️  Inicializando base de datos completa...")
    
    # ¡CAMBIO! Usa el objeto 'settings' directamente
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=settings.PROXY_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    # Crear tablas principales
    print("Creando tablas...")
    
    # 1. Perfiles de clientes
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS customer_profiles (
            id SERIAL PRIMARY KEY,
            customer_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            tier VARCHAR(20) DEFAULT 'Basic',
            join_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            satisfaction_score FLOAT DEFAULT 3.0,
            total_interactions INTEGER DEFAULT 0,
            preferred_channel VARCHAR(20) DEFAULT 'chat',
            language VARCHAR(10) DEFAULT 'es',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_customer_profiles_customer_id ON customer_profiles(customer_id);
    ''')
    
    # 2. Interacciones de clientes
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS customer_interactions (
            id SERIAL PRIMARY KEY,
            customer_id VARCHAR(50) NOT NULL REFERENCES customer_profiles(customer_id),
            interaction_type VARCHAR(20) NOT NULL,
            issue_type VARCHAR(50),
            message TEXT,
            sentiment VARCHAR(20),
            priority_level VARCHAR(20),
            resolved BOOLEAN DEFAULT FALSE,
            resolution_time FLOAT,
            agent_id VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_interactions_customer_id ON customer_interactions(customer_id);
        CREATE INDEX IF NOT EXISTS idx_interactions_created_at ON customer_interactions(created_at);
    ''')
    
    # 3. Base de conocimientos con vectores
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,
            category VARCHAR(50),
            subcategory VARCHAR(100),
            solution_steps JSONB,
            estimated_time INTEGER,
            escalation_needed BOOLEAN DEFAULT FALSE,
            follow_up_required BOOLEAN DEFAULT FALSE,
            embedding vector(768),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category);
    ''')
    
    # 4. Cache de análisis de sentimiento
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_cache (
            id SERIAL PRIMARY KEY,
            message_hash VARCHAR(64) UNIQUE NOT NULL,
            primary_sentiment VARCHAR(20),
            urgency_level VARCHAR(20),
            escalation_risk VARCHAR(20),
            emotional_intensity FLOAT,
            confidence_score FLOAT,
            detected_keywords JSONB,
            recommended_tone VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_sentiment_cache_hash ON sentiment_cache(message_hash);
    ''')
    
    # 5. Reglas de priorización
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS priority_rules (
            id SERIAL PRIMARY KEY,
            rule_name VARCHAR(100) NOT NULL,
            condition JSONB,
            priority_adjustment INTEGER,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    ''')
    
    print("Todas las tablas creadas")
    
    # Insertar datos de ejemplo
    print("Insertando datos de ejemplo...")
    
    # Clientes (migrar datos existentes de las tools)
    customers_data = [
        ('CUST_001', 'María González', 'Premium', 4.2, 12, 'chat'),
        ('CUST_002', 'Juan Pérez', 'Basic', 3.8, 3, 'email'),
        ('CUST_003', 'Ana López', 'Gold', 4.5, 8, 'phone')
    ]
    
    for customer_id, name, tier, satisfaction, interactions, channel in customers_data:
        await conn.execute('''
            INSERT INTO customer_profiles (customer_id, name, tier, satisfaction_score, total_interactions, preferred_channel)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (customer_id) DO UPDATE SET
                name = EXCLUDED.name,
                tier = EXCLUDED.tier,
                satisfaction_score = EXCLUDED.satisfaction_score,
                total_interactions = EXCLUDED.total_interactions,
                preferred_channel = EXCLUDED.preferred_channel,
                updated_at = NOW()
        ''', customer_id, name, tier, satisfaction, interactions, channel)
    
    # Base de conocimientos (migrar de tools existentes)
    kb_data = [
        (
            'Resolución de Cargo Duplicado',
            'Procedimiento completo para resolver cargos duplicados en tarjetas de crédito de clientes.',
            'facturación',
            'cargo_duplicado',
            '["1. Verificar todas las transacciones en el sistema de facturación", "2. Confirmar fechas y montos con el cliente", "3. Identificar si es cargo legítimo o duplicado real", "4. Si es duplicado: procesar reembolso inmediato", "5. Actualizar información de facturación del cliente", "6. Configurar alertas para prevenir futuros duplicados"]',
            15,
            False,
            True
        ),
        (
            'Servicio No Funciona - Diagnóstico Técnico',
            'Diagnóstico y resolución paso a paso de problemas técnicos cuando el servicio no funciona.',
            'técnico',
            'servicio_no_funciona',
            '["1. Verificar estado general del servicio en la región del cliente", "2. Solicitar al cliente que reinicie su conexión/dispositivo", "3. Verificar configuración específica del cliente", "4. Ejecutar diagnósticos remotos del servicio", "5. Si persiste: escalar a soporte técnico nivel 2", "6. Proporcionar número de ticket para seguimiento"]',
            25,
            True,
            True
        ),
        (
            'Conectividad Intermitente',
            'Resolución de problemas de conectividad intermitente y optimización de conexión.',
            'técnico',
            'conectividad_intermitente',
            '["1. Ejecutar diagnóstico completo de red del cliente", "2. Verificar calidad y estabilidad de la conexión", "3. Revisar configuraciones de red del cliente", "4. Optimizar parámetros de conexión", "5. Programar monitoreo adicional por 24 horas", "6. Proveer reporte de monitoreo al cliente"]',
            20,
            False,
            True
        ),
        (
            'Consulta de Información de Cuenta',
            'Procedimiento estándar para consultas de información de cuenta de cliente.',
            'general',
            'informacion_cuenta',
            '["1. Verificar identidad del cliente", "2. Acceder a información de cuenta solicitada", "3. Proporcionar información de manera segura", "4. Explicar cualquier término o condición relevante", "5. Ofrecer servicios adicionales si aplica"]',
            10,
            False,
            False
        )
    ]
    
    for title, content, category, subcategory, steps, time, escalation, followup in kb_data:
        await conn.execute('''
            INSERT INTO knowledge_base (title, content, category, subcategory, solution_steps, estimated_time, escalation_needed, follow_up_required)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)
            ON CONFLICT DO NOTHING
        ''', title, content, category, subcategory, steps, time, escalation, followup)
    
    # Verificar datos insertados
    customer_count = await conn.fetchval("SELECT COUNT(*) FROM customer_profiles;")
    kb_count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base;")
    table_count = await conn.fetchval("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    
    print(f"Tablas creadas: {table_count}")
    print(f"Clientes migrados: {customer_count}")
    print(f"Artículos KB: {kb_count}")
    
    # Verificar extensión pgvector
    vector_ext = await conn.fetchval("SELECT extname FROM pg_extension WHERE extname = 'vector';")
    if vector_ext:
        print("Extensión pgvector: Habilitada")
    else:
        print("Extensión pgvector: No encontrada")
    
    await conn.close()
    print("\n Base de datos completamente inicializada!")
    print(" Datos migrados de herramientas existentes")
    print("Soporte para vectores habilitado")
    print("Índices optimizados creados")

if __name__ == "__main__":
    asyncio.run(init_database())