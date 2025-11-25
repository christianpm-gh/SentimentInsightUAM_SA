
import sys
from pathlib import Path
import asyncio
import pprint

# Agregar directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.db import init_all_databases, close_all_databases, get_mongo_db

async def verificar_mongo():
    await init_all_databases()
    try:
        db = get_mongo_db()
        collection = db['opiniones']
        
        # Buscar documentos analizados
        cursor = collection.find({"sentimiento_general.analizado": True}).limit(3)
        
        print("="*80)
        print("VERIFICACIÓN DE DATOS EN MONGODB")
        print("="*80)
        
        count = 0
        async for doc in cursor:
            count += 1
            print(f"\n--- Documento {count} (ID: {doc['_id']}) ---")
            print(f"Profesor ID: {doc.get('profesor_id')}")
            print(f"Comentario: {doc.get('comentario')[:100]}...")
            
            sentimiento = doc.get('sentimiento_general', {})
            print("\n[Sentimiento General]")
            pprint.pprint(sentimiento)
            
            categorizacion = doc.get('categorizacion', {})
            print("\n[Categorización]")
            pprint.pprint(categorizacion)
            
        if count == 0:
            print("\nNo se encontraron documentos analizados.")
        else:
            print(f"\nSe mostraron {count} documentos de muestra.")
            
    finally:
        await close_all_databases()

if __name__ == "__main__":
    asyncio.run(verificar_mongo())
