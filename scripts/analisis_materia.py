#!/usr/bin/env python3
"""
Script para ver análisis completo de una materia/curso.

Uso:
    python scripts/analisis_materia.py "Estructura de Datos"
    python scripts/analisis_materia.py "Programación"
"""

import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
import argparse
from src.db import init_all_databases, close_all_databases, get_mongo_db


async def analisis_materia(nombre_materia: str):
    """Muestra análisis completo de una materia."""
    await init_all_databases()
    
    try:
        db = get_mongo_db()
        opiniones = db['opiniones']
        
        # Buscar opiniones de la materia (búsqueda parcial)
        total = await opiniones.count_documents({
            "curso": {"$regex": nombre_materia, "$options": "i"}
        })
        
        if total == 0:
            print(f"✗ No se encontraron opiniones para la materia: {nombre_materia}")
            return
        
        print("="*80)
        print("ANÁLISIS DE MATERIA/CURSO")
        print("="*80)
        print()
        print(f"Materia: {nombre_materia}")
        print()
        
        sent_analizadas = await opiniones.count_documents({
            "curso": {"$regex": nombre_materia, "$options": "i"},
            "sentimiento_general.analizado": True
        })
        
        cat_analizadas = await opiniones.count_documents({
            "curso": {"$regex": nombre_materia, "$options": "i"},
            "categorizacion.analizado": True
        })
        
        print("-"*80)
        print("ESTADÍSTICAS GENERALES")
        print("-"*80)
        print(f"Total de opiniones: {total}")
        print(f"Sentimiento analizado: {sent_analizadas} ({sent_analizadas/total*100 if total > 0 else 0:.1f}%)")
        print(f"Categorización analizada: {cat_analizadas} ({cat_analizadas/total*100 if total > 0 else 0:.1f}%)")
        print()
        
        if sent_analizadas > 0:
            # Distribución de sentimientos
            positivas = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "sentimiento_general.clasificacion": "positivo"
            })
            neutrales = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "sentimiento_general.clasificacion": "neutral"
            })
            negativas = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "sentimiento_general.clasificacion": "negativo"
            })
            
            print("-"*80)
            print("DISTRIBUCIÓN DE SENTIMIENTOS")
            print("-"*80)
            print(f"Positivas: {positivas:>3} ({positivas/sent_analizadas*100:.1f}%)")
            print(f"Neutrales: {neutrales:>3} ({neutrales/sent_analizadas*100:.1f}%)")
            print(f"Negativas: {negativas:>3} ({negativas/sent_analizadas*100:.1f}%)")
            print()
        
        if cat_analizadas > 0:
            print("-"*80)
            print("CATEGORIZACIÓN DETALLADA")
            print("-"*80)
            
            # Calidad didáctica
            cal_pos = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "categorizacion.calidad_didactica.valoracion": "positivo"
            })
            cal_neu = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "categorizacion.calidad_didactica.valoracion": "neutral"
            })
            cal_neg = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "categorizacion.calidad_didactica.valoracion": "negativo"
            })
            
            print(f"Calidad Didáctica:")
            print(f"  Positivo: {cal_pos:>3} ({cal_pos/cat_analizadas*100:.1f}%)")
            print(f"  Neutral:  {cal_neu:>3} ({cal_neu/cat_analizadas*100:.1f}%)")
            print(f"  Negativo: {cal_neg:>3} ({cal_neg/cat_analizadas*100:.1f}%)")
            print()
            
            # Método evaluación
            met_pos = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "categorizacion.metodo_evaluacion.valoracion": "positivo"
            })
            met_neu = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "categorizacion.metodo_evaluacion.valoracion": "neutral"
            })
            met_neg = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "categorizacion.metodo_evaluacion.valoracion": "negativo"
            })
            
            print(f"Método de Evaluación:")
            print(f"  Positivo: {met_pos:>3} ({met_pos/cat_analizadas*100:.1f}%)")
            print(f"  Neutral:  {met_neu:>3} ({met_neu/cat_analizadas*100:.1f}%)")
            print(f"  Negativo: {met_neg:>3} ({met_neg/cat_analizadas*100:.1f}%)")
            print()
            
            # Empatía
            emp_pos = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "categorizacion.empatia.valoracion": "positivo"
            })
            emp_neu = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "categorizacion.empatia.valoracion": "neutral"
            })
            emp_neg = await opiniones.count_documents({
                "curso": {"$regex": nombre_materia, "$options": "i"},
                "categorizacion.empatia.valoracion": "negativo"
            })
            
            print(f"Empatía:")
            print(f"  Positivo: {emp_pos:>3} ({emp_pos/cat_analizadas*100:.1f}%)")
            print(f"  Neutral:  {emp_neu:>3} ({emp_neu/cat_analizadas*100:.1f}%)")
            print(f"  Negativo: {emp_neg:>3} ({emp_neg/cat_analizadas*100:.1f}%)")
            print()
        
        # Profesores que imparten la materia
        print("-"*80)
        print("PROFESORES QUE IMPARTEN LA MATERIA")
        print("-"*80)
        
        pipeline = [
            {"$match": {"curso": {"$regex": nombre_materia, "$options": "i"}}},
            {"$group": {"_id": "$profesor_nombre", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        cursor = opiniones.aggregate(pipeline)
        
        async for doc in cursor:
            profesor = doc['_id']
            count = doc['count']
            print(f"  • {profesor} ({count} opiniones)")
        
        print()
        
        # Muestra de opinión
        doc = await opiniones.find_one({
            "curso": {"$regex": nombre_materia, "$options": "i"},
            "sentimiento_general.analizado": True
        })
        
        if doc:
            print("-"*80)
            print("MUESTRA DE OPINIÓN")
            print("-"*80)
            comentario = doc.get('comentario', '')[:200]
            print(f'"{comentario}..."')
            sent = doc.get('sentimiento_general', {})
            print(f"Sentimiento: {sent.get('clasificacion', 'N/A').upper()} (confianza: {sent.get('confianza', 0):.2f})")
            print(f"Profesor: {doc.get('profesor_nombre', 'N/A')}")
            print()
        
        print("="*80)
    
    finally:
        await close_all_databases()


def main():
    parser = argparse.ArgumentParser(
        description="Muestra análisis completo de una materia/curso"
    )
    parser.add_argument(
        "materia",
        type=str,
        help="Nombre de la materia/curso"
    )
    
    args = parser.parse_args()
    asyncio.run(analisis_materia(args.materia))


if __name__ == "__main__":
    main()
