#!/usr/bin/env python3
"""
Script para ver detalles de una opinión específica.

Uso:
    python scripts/ver_opinion.py <opinion_id>
    python scripts/ver_opinion.py 507f1f77bcf86cd799439011
"""

import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
import argparse
from bson import ObjectId
from src.db import init_all_databases, close_all_databases, get_mongo_db


async def ver_opinion(opinion_id: str):
    """Muestra detalles completos de una opinión."""
    await init_all_databases()
    
    try:
        db = get_mongo_db()
        opiniones = db['opiniones']
        
        # Buscar opinión
        try:
            doc = await opiniones.find_one({"_id": ObjectId(opinion_id)})
        except:
            print(f"✗ Error: '{opinion_id}' no es un ObjectId válido")
            return
        
        if not doc:
            print(f"✗ No se encontró opinión con ID: {opinion_id}")
            return
        
        print("="*80)
        print("DETALLES DE LA OPINIÓN")
        print("="*80)
        print()
        
        # Información básica
        print(f"ID: {doc['_id']}")
        print(f"Profesor: {doc.get('profesor_nombre', 'N/A')} (ID: {doc.get('profesor_id', 'N/A')})")
        print(f"Curso: {doc.get('curso', 'N/A')}")
        print(f"Fecha: {doc.get('fecha_opinion', 'N/A')}")
        print()
        
        # Comentario
        print("-"*80)
        print("COMENTARIO:")
        print("-"*80)
        print(doc.get('comentario', 'Sin comentario'))
        print()
        
        # Análisis de sentimiento
        sent = doc.get('sentimiento_general', {})
        if sent.get('analizado'):
            print("-"*80)
            print("SENTIMIENTO GENERAL:")
            print("-"*80)
            print(f"Clasificación: {sent.get('clasificacion', 'N/A').upper()}")
            print(f"Confianza: {sent.get('confianza', 0):.3f}")
            
            pesos = sent.get('pesos', {})
            print(f"Pesos:")
            print(f"  - Positivo: {pesos.get('positivo', 0):.3f}")
            print(f"  - Neutral:  {pesos.get('neutral', 0):.3f}")
            print(f"  - Negativo: {pesos.get('negativo', 0):.3f}")
            
            print(f"Modelo: {sent.get('modelo_version', 'N/A')}")
            print(f"Fecha análisis: {sent.get('fecha_analisis', 'N/A')}")
            print()
        else:
            print("⚠ Sentimiento: NO ANALIZADO")
            print()
        
        # Categorización
        cat = doc.get('categorizacion', {})
        if cat.get('analizado'):
            print("-"*80)
            print("CATEGORIZACIÓN:")
            print("-"*80)
            
            # Calidad didáctica
            cal_did = cat.get('calidad_didactica', {})
            print(f"Calidad Didáctica: {cal_did.get('valoracion', 'N/A').upper()}")
            print(f"  Confianza: {cal_did.get('confianza', 0):.3f}")
            if cal_did.get('palabras_clave'):
                print(f"  Palabras: {', '.join(cal_did.get('palabras_clave', []))}")
            
            # Método evaluación
            met_eval = cat.get('metodo_evaluacion', {})
            print(f"Método Evaluación: {met_eval.get('valoracion', 'N/A').upper()}")
            print(f"  Confianza: {met_eval.get('confianza', 0):.3f}")
            if met_eval.get('palabras_clave'):
                print(f"  Palabras: {', '.join(met_eval.get('palabras_clave', []))}")
            
            # Empatía
            emp = cat.get('empatia', {})
            print(f"Empatía: {emp.get('valoracion', 'N/A').upper()}")
            print(f"  Confianza: {emp.get('confianza', 0):.3f}")
            if emp.get('palabras_clave'):
                print(f"  Palabras: {', '.join(emp.get('palabras_clave', []))}")
            
            print(f"Modelo: {cat.get('modelo_version', 'N/A')}")
            print()
        else:
            print("⚠ Categorización: NO ANALIZADA")
            print()
        
        print("="*80)
    
    finally:
        await close_all_databases()


def main():
    parser = argparse.ArgumentParser(
        description="Muestra detalles completos de una opinión"
    )
    parser.add_argument(
        "opinion_id",
        type=str,
        help="ObjectId de la opinión en MongoDB"
    )
    
    args = parser.parse_args()
    asyncio.run(ver_opinion(args.opinion_id))


if __name__ == "__main__":
    main()
