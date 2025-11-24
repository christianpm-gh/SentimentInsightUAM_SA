#!/usr/bin/env python3
"""
Script para listar profesores disponibles en la base de datos.

Uso:
    python scripts/listar_profesores.py
    python scripts/listar_profesores.py --limit 50
    python scripts/listar_profesores.py --departamento Sistemas
"""

import sys
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import asyncio
import argparse
from src.db import init_all_databases, close_all_databases, AsyncSessionLocal
from src.db.models import Profesor
from sqlalchemy import select, func


async def listar_profesores(limit: int = 20, departamento: str = None):
    """Lista profesores de PostgreSQL con sus estadísticas."""
    await init_all_databases()
    
    try:
        async with AsyncSessionLocal() as session:
            # Construir query
            query = select(Profesor).where(Profesor.activo == True)
            
            if departamento:
                query = query.where(Profesor.departamento == departamento)
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            profesores = result.scalars().all()
            
            print("="*80)
            print("PROFESORES DISPONIBLES")
            print("="*80)
            print()
            
            if not profesores:
                print("No se encontraron profesores.")
                return
            
            print(f"{'ID':<6} {'Nombre':<50} {'Departamento':<15}")
            print("-"*80)
            
            for p in profesores:
                nombre = p.nombre_completo[:47] + "..." if len(p.nombre_completo) > 50 else p.nombre_completo
                print(f"{p.id:<6} {nombre:<50} {p.departamento:<15}")
            
            print()
            print(f"Total: {len(profesores)} profesores")
            print("="*80)
    
    finally:
        await close_all_databases()


def main():
    parser = argparse.ArgumentParser(
        description="Lista profesores disponibles en la base de datos"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Número máximo de profesores a mostrar (default: 20)"
    )
    parser.add_argument(
        "--departamento",
        type=str,
        help="Filtrar por departamento (ej: Sistemas)"
    )
    
    args = parser.parse_args()
    asyncio.run(listar_profesores(args.limit, args.departamento))


if __name__ == "__main__":
    main()
