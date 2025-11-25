#!/usr/bin/env python3
"""
Script para procesar categorización de opiniones pendientes.

Este script procesa las opiniones que ya tienen análisis de sentimiento
pero les falta la categorización (calidad_didactica, empatia, metodo_evaluacion).

Uso:
    python scripts/procesar_categorizacion.py
    python scripts/procesar_categorizacion.py --limit 100
    python scripts/procesar_categorizacion.py --batch-size 20

Autor: SentimentInsightUAM Team
Fecha: 2025-11
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Agregar directorio raíz al PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import logging
from src.db import init_all_databases, close_all_databases, get_mongo_db
from src.db.repository import (
    obtener_opiniones_pendientes_categorizacion,
    contar_opiniones_pendientes_categorizacion,
    actualizar_categorizacion
)
from src.ml.categorizer import get_categorizer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def procesar_categorizacion(limit: int = -1, batch_size: int = 50):
    """
    Procesa categorización de opiniones pendientes.
    
    Args:
        limit: Máximo de opiniones a procesar (-1 para todas)
        batch_size: Tamaño de batch para procesamiento
    """
    print("\n" + "="*80)
    print("ANÁLISIS DE CATEGORIZACIÓN - Opiniones Pendientes")
    print("(Calidad Didáctica, Empatía, Método de Evaluación)")
    print("="*80 + "\n")
    
    await init_all_databases()
    
    try:
        # Contar pendientes
        total_pendientes = await contar_opiniones_pendientes_categorizacion()
        print(f"Total de opiniones pendientes de categorización: {total_pendientes}")
        
        if total_pendientes == 0:
            print("\n✓ No hay opiniones pendientes de categorización")
            return
        
        # Determinar cuántas procesar
        to_process = total_pendientes if limit < 0 else min(limit, total_pendientes)
        print(f"Procesando {to_process} opiniones en batches de {batch_size}...")
        print()
        
        # Inicializar categorizador
        categorizer = get_categorizer()
        print(f"Modelo: {categorizer.get_version()}")
        print()
        
        # Procesar en batches
        processed = 0
        exitosas = 0
        errores = 0
        
        while processed < to_process:
            # Obtener batch de opiniones
            current_batch_size = min(batch_size, to_process - processed)
            opiniones = await obtener_opiniones_pendientes_categorizacion(
                limit=current_batch_size,
                skip=0  # Siempre 0 porque las vamos marcando como procesadas
            )
            
            if not opiniones:
                break
            
            # Extraer textos
            textos = [op.get("comentario", "") for op in opiniones]
            opinion_ids = [str(op["_id"]) for op in opiniones]
            
            # Categorizar batch
            resultados = categorizer.categorizar_batch(textos)
            
            # Actualizar MongoDB
            for opinion_id, resultado in zip(opinion_ids, resultados):
                try:
                    actualizado = await actualizar_categorizacion(
                        opinion_id=opinion_id,
                        calidad_didactica=resultado.calidad_didactica,
                        metodo_evaluacion=resultado.metodo_evaluacion,
                        empatia=resultado.empatia,
                        modelo_version=categorizer.get_version(),
                        tiempo_procesamiento_ms=resultado.tiempo_ms
                    )
                    
                    if actualizado:
                        exitosas += 1
                    else:
                        errores += 1
                        
                except Exception as e:
                    errores += 1
                    logger.error(f"Error en opinión {opinion_id}: {e}")
            
            processed += len(opiniones)
            
            # Mostrar progreso
            pct = (processed / to_process) * 100
            print(f"  [{processed}/{to_process}] {pct:.1f}% completado - "
                  f"Exitosas: {exitosas}, Errores: {errores}")
        
        # Resultados finales
        print("\n" + "="*80)
        print("RESULTADO DE LA CATEGORIZACIÓN")
        print("="*80)
        print(f"  Opiniones procesadas: {processed}")
        print(f"  Categorizaciones exitosas: {exitosas}")
        print(f"  Errores: {errores}")
        
        if exitosas > 0:
            print(f"\n  Tasa de éxito: {exitosas / processed * 100:.1f}%")
        
        # Verificar pendientes restantes
        pendientes_restantes = await contar_opiniones_pendientes_categorizacion()
        print(f"\n  Opiniones pendientes restantes: {pendientes_restantes}")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Error en procesamiento: {e}", exc_info=True)
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)
        
    finally:
        await close_all_databases()


async def verificar_ejemplo():
    """Muestra un ejemplo de opinión categorizada."""
    await init_all_databases()
    
    try:
        db = get_mongo_db()
        collection = db['opiniones']
        
        # Buscar una opinión con categorización completa
        doc = await collection.find_one({
            "categorizacion.analizado": True
        })
        
        if doc:
            print("\n" + "="*80)
            print("EJEMPLO DE OPINIÓN CATEGORIZADA:")
            print("="*80)
            print(f"\nID: {doc['_id']}")
            print(f"Comentario: {doc.get('comentario', '')[:200]}...")
            print(f"\nCategorización:")
            cat = doc.get('categorizacion', {})
            
            for campo in ['calidad_didactica', 'empatia', 'metodo_evaluacion']:
                if campo in cat:
                    datos = cat[campo]
                    print(f"\n  {campo.upper().replace('_', ' ')}:")
                    print(f"    Valoración: {datos.get('valoracion', 'N/A')}")
                    print(f"    Confianza: {datos.get('confianza', 'N/A')}")
                    print(f"    Palabras clave: {datos.get('palabras_clave', [])}")
            
            print("="*80 + "\n")
        else:
            print("\nNo hay opiniones con categorización completa aún.")
            
    finally:
        await close_all_databases()


def main():
    parser = argparse.ArgumentParser(
        description="Procesar categorización de opiniones pendientes"
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=-1,
        help='Máximo de opiniones a procesar (-1 para todas)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Tamaño de batch para procesamiento (default: 50)'
    )
    parser.add_argument(
        '--verificar',
        action='store_true',
        help='Solo muestra un ejemplo de opinión categorizada'
    )
    
    args = parser.parse_args()
    
    if args.verificar:
        asyncio.run(verificar_ejemplo())
    else:
        asyncio.run(procesar_categorizacion(
            limit=args.limit,
            batch_size=args.batch_size
        ))


if __name__ == "__main__":
    main()
