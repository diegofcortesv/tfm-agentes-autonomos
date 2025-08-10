# scripts/enable_pgvector.py
import asyncio
import asyncpg
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import settings

async def enable_pgvector():
    
    connection_params = {
        "host": "127.0.0.1",
        "port": settings.PROXY_PORT,
        "database": settings.DB_NAME,
        "user": "postgres", 
        "password": settings.DB_ROOT_PASSWORD
    }
    
    try:
        print(f"Conectando a PostgreSQL via proxy (puerto {settings.PROXY_PORT})...")
        conn = await asyncpg.connect(**connection_params)
        
        print("Habilitando extensión pgvector...")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        print("Verificando instalación...")
        result = await conn.fetch("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        
        if result:
            print("pgvector habilitado correctamente!")
            print(f"   Extensión encontrada: {result[0]['extname']}")
            
            # Probar funcionalidad básica
            print("Probando funcionalidad de vectores...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS test_vectors (
                    id SERIAL PRIMARY KEY,
                    embedding vector(3)
                );
            """)
            
            await conn.execute("INSERT INTO test_vectors (embedding) VALUES ($1);", [0.1, 0.2, 0.3])
            
            result = await conn.fetchval("SELECT embedding FROM test_vectors ORDER BY id DESC LIMIT 1;")
            print(f"Vector de prueba insertado: {result}")
            
            await conn.execute("DROP TABLE test_vectors;")
            print("Funcionalidad de vectores verificada!")
            
        else:
            print("No se pudo verificar la instalación de pgvector")
            return False
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(enable_pgvector())
    if success:
        print("\npgvector configurado correctamente!")
        print("   Siguiente paso: Inicializar base de datos")
    else:
        print("\nError configurando pgvector")
