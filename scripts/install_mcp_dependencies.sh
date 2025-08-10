#!/bin/bash
# Script para instalar dependencias MCP y embeddings

echo "📦 Instalando dependencias para MCP y búsqueda semántica..."

# Instalar paquetes necesarios para MCP
pip install \
    mcp==1.0.0 \
    sentence-transformers==2.2.2 \
    chromadb==0.4.18 \
    numpy==1.24.3 \
    scikit-learn==1.3.0 \
    transformers==4.35.0 \
    torch==2.1.0

# Verificar instalación
echo "✅ Verificando instalación..."

python -c "
try:
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    print('✅ sentence-transformers: OK')
    
    import numpy as np
    print('✅ numpy: OK')
    
    import sklearn
    print('✅ scikit-learn: OK')
    
    # Test básico de modelo de embeddings
    print('🧪 Probando modelo de embeddings...')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    test_embedding = model.encode(['Test sentence'])
    print(f'✅ Embedding generado: dimensión {len(test_embedding[0])}')
    
    print('🎉 Todas las dependencias MCP instaladas correctamente!')
    
except ImportError as e:
    print(f'❌ Error: {e}')
    print('Reintenta la instalación')
"

echo "📋 Dependencias instaladas para:"
echo "   - Model Context Protocol (MCP)"
echo "   - Sentence Transformers (embeddings)"
echo "   - Búsqueda semántica vectorial"
echo "   - RAG (Retrieval Augmented Generation)"