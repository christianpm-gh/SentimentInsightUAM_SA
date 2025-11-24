#!/usr/bin/env python3
"""
Script para listar materias/cursos disponibles en la base de datos.

Uso:
    python scripts/listar_materias.py
    python scripts/listar_materias.py --limit 30
    python scripts/listar_materias.py --con-opiniones
"""

import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
import argparse
from src.db import init_all_databases, close_all_databases, get_mongo_db


async def listar_materias(limit: int = 20, con_opiniones: bool = False):
    """Lista materias/cursos de MongoDB con conteo de opiniones."""
    await init_all_databases()
    
    try:
        db = get_mongo_db()
        opiniones = db['opiniones']
        
        print("="*80)
        print("MATERIAS/CURSOS DISPONIBLES")
        print("="*80)
        print()
        
        # Agregación para contar opiniones por curso (excluyendo cursos sin nombre)
        pipeline = [
            {"$match": {"curso": {"$nin": ["---", "", None, "N/A", "Sin curso"]}}},
            {"$group": {"_id": "$curso", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        cursor = opiniones.aggregate(pipeline)
        
        print(f"{'#':<4} {'Materia':<55} {'Opiniones':>10}")
        print("-"*80)
        
        count = 1
        total_opiniones = 0
        
        async for doc in cursor:
            curso = doc['_id']
            total = doc['count']
            total_opiniones += total
            
            # Truncar nombre si es muy largo
            curso_display = curso[:52] + "..." if len(curso) > 55 else curso
            
            print(f"{count:<4} {curso_display:<55} {total:>10}")
            count += 1
        
        print()
        print(f"Total: {count-1} materias | {total_opiniones} opiniones")
        
        # Mostrar información sobre cursos sin nombre
        sin_nombre = await opiniones.count_documents({
            "curso": {"$in": ["---", "", None, "N/A", "Sin curso"]}
        })
        
        if sin_nombre > 0:
            print()
            print(f"⚠ Nota: {sin_nombre} opiniones sin nombre de curso (excluidas)")
        
        print("="*80)
    
    finally:
        await close_all_databases()


def main():
    parser = argparse.ArgumentParser(
        description="Lista materias/cursos disponibles en la base de datos"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Número máximo de materias a mostrar (default: 20)"
    )
    parser.add_argument(
        "--con-opiniones",
        action="store_true",
        help="Mostrar solo materias con opiniones analizadas"
    )
    
    args = parser.parse_args()
    asyncio.run(listar_materias(args.limit, args.con_opiniones))


if __name__ == "__main__":
    main()
