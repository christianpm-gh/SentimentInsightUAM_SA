#!/usr/bin/env python3
"""
Script para ver análisis completo de un profesor.

Uso:
    python scripts/analisis_profesor.py <profesor_id>
    python scripts/analisis_profesor.py 36
    python scripts/analisis_profesor.py --nombre "Josue Padilla"
"""

import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
import argparse
from src.db import init_all_databases, close_all_databases, AsyncSessionLocal, get_mongo_db
from src.db.models import Profesor
from sqlalchemy import select


async def analisis_profesor(profesor_id: int = None, nombre: str = None):
    """Muestra análisis completo de un profesor."""
    await init_all_databases()
    
    try:
        # Buscar profesor
        async with AsyncSessionLocal() as session:
            if profesor_id:
                result = await session.execute(
                    select(Profesor).where(Profesor.id == profesor_id)
                )
            elif nombre:
                result = await session.execute(
                    select(Profesor).where(
                        Profesor.nombre_completo.ilike(f"%{nombre}%")
                    )
                )
            else:
                print("✗ Debes proporcionar --id o --nombre")
                return
            
            profesor = result.scalars().first()
            
            if not profesor:
                print(f"✗ No se encontró profesor")
                return
            
            print("="*80)
            print("ANÁLISIS DE PROFESOR")
            print("="*80)
            print()
            print(f"ID: {profesor.id}")
            print(f"Nombre: {profesor.nombre_completo}")
            print(f"Departamento: {profesor.departamento}")
            print(f"Slug: {profesor.slug}")
            print()
        
        # Obtener estadísticas de MongoDB
        db = get_mongo_db()
        opiniones = db['opiniones']
        
        total = await opiniones.count_documents({"profesor_id": profesor.id})
        
        sent_analizadas = await opiniones.count_documents({
            "profesor_id": profesor.id,
            "sentimiento_general.analizado": True
        })
        
        cat_analizadas = await opiniones.count_documents({
            "profesor_id": profesor.id,
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
                "profesor_id": profesor.id,
                "sentimiento_general.clasificacion": "positivo"
            })
            neutrales = await opiniones.count_documents({
                "profesor_id": profesor.id,
                "sentimiento_general.clasificacion": "neutral"
            })
            negativas = await opiniones.count_documents({
                "profesor_id": profesor.id,
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
                "profesor_id": profesor.id,
                "categorizacion.calidad_didactica.valoracion": "positivo"
            })
            cal_neu = await opiniones.count_documents({
                "profesor_id": profesor.id,
                "categorizacion.calidad_didactica.valoracion": "neutral"
            })
            cal_neg = await opiniones.count_documents({
                "profesor_id": profesor.id,
                "categorizacion.calidad_didactica.valoracion": "negativo"
            })
            
            print(f"Calidad Didáctica:")
            print(f"  Positivo: {cal_pos:>3} ({cal_pos/cat_analizadas*100:.1f}%)")
            print(f"  Neutral:  {cal_neu:>3} ({cal_neu/cat_analizadas*100:.1f}%)")
            print(f"  Negativo: {cal_neg:>3} ({cal_neg/cat_analizadas*100:.1f}%)")
            print()
            
            # Método evaluación
            met_pos = await opiniones.count_documents({
                "profesor_id": profesor.id,
                "categorizacion.metodo_evaluacion.valoracion": "positivo"
            })
            met_neu = await opiniones.count_documents({
                "profesor_id": profesor.id,
                "categorizacion.metodo_evaluacion.valoracion": "neutral"
            })
            met_neg = await opiniones.count_documents({
                "profesor_id": profesor.id,
                "categorizacion.metodo_evaluacion.valoracion": "negativo"
            })
            
            print(f"Método de Evaluación:")
            print(f"  Positivo: {met_pos:>3} ({met_pos/cat_analizadas*100:.1f}%)")
            print(f"  Neutral:  {met_neu:>3} ({met_neu/cat_analizadas*100:.1f}%)")
            print(f"  Negativo: {met_neg:>3} ({met_neg/cat_analizadas*100:.1f}%)")
            print()
            
            # Empatía
            emp_pos = await opiniones.count_documents({
                "profesor_id": profesor.id,
                "categorizacion.empatia.valoracion": "positivo"
            })
            emp_neu = await opiniones.count_documents({
                "profesor_id": profesor.id,
                "categorizacion.empatia.valoracion": "neutral"
            })
            emp_neg = await opiniones.count_documents({
                "profesor_id": profesor.id,
                "categorizacion.empatia.valoracion": "negativo"
            })
            
            print(f"Empatía:")
            print(f"  Positivo: {emp_pos:>3} ({emp_pos/cat_analizadas*100:.1f}%)")
            print(f"  Neutral:  {emp_neu:>3} ({emp_neu/cat_analizadas*100:.1f}%)")
            print(f"  Negativo: {emp_neg:>3} ({emp_neg/cat_analizadas*100:.1f}%)")
            print()
        
        # Muestra de opinión
        doc = await opiniones.find_one({
            "profesor_id": profesor.id,
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
            print()
        
        print("="*80)
    
    finally:
        await close_all_databases()


def main():
    parser = argparse.ArgumentParser(
        description="Muestra análisis completo de un profesor"
    )
    parser.add_argument(
        "profesor_id",
        type=int,
        nargs="?",
        help="ID del profesor"
    )
    parser.add_argument(
        "--nombre",
        type=str,
        help="Buscar por nombre del profesor"
    )
    
    args = parser.parse_args()
    
    if not args.profesor_id and not args.nombre:
        parser.print_help()
        return
    
    asyncio.run(analisis_profesor(args.profesor_id, args.nombre))


if __name__ == "__main__":
    main()
