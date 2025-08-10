# tests/test_vectors.py
import asyncio
import asyncpg
import sys
import os


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import settings

async def test_pgvector():
    
    
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=settings.PROXY_PORT,
        database=settings.DB_NAME, 
        user="postgres", # Se conecta como root para la prueba
        password=settings.DB_ROOT_PASSWORD
    )
    
    print(" Probando funcionalidad de vectores...")
    
    # Crear tabla de test
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS test_vectors (
            id SERIAL PRIMARY KEY,
            embedding vector(3)
        );
    """)
    
    # Insertar vector (formato correcto para asyncpg)
    vector_data = "[0.1,0.2,0.3]"  # Como string
    await conn.execute("INSERT INTO test_vectors (embedding) VALUES ($1);", vector_data)
    
    # Consultar vector
    result = await conn.fetchval("SELECT embedding FROM test_vectors ORDER BY id DESC LIMIT 1;")
    print(f"Vector de prueba insertado: {result}")
    
    # Limpiar
    await conn.execute("DROP TABLE test_vectors;")
    
    await conn.close()
    print("pgvector funcionando correctamente!")

if __name__ == "__main__":    
    asyncio.run(test_pgvector())