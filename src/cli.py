"""
CLI para SentimentInsightUAM_SA - Análisis de Sentimientos

Comandos disponibles:
- analizar: Analiza opiniones pendientes de sentimiento
- profesor: Analiza opiniones de un profesor específico
- curso: Analiza opiniones de un curso específico
- stats: Muestra estadísticas de análisis

Autor: SentimentInsightUAM Team
Fecha: 2025-11-09
"""

import asyncio
import sys
import argparse
import logging
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports de módulos del proyecto
from src.db import init_all_databases, close_all_databases
from src.ml.processor import OpinionProcessor


# ============================================================================
# COMANDOS
# ============================================================================

async def comando_analizar(args):
    """
    Comando para analizar opiniones pendientes de sentimiento general.
    
    Args:
        args: Argumentos de línea de comandos
    """
    print("\n" + "="*80)
    print("ANÁLISIS DE SENTIMIENTO - Opiniones Pendientes")
    print("="*80 + "\n")
    
    try:
        # Inicializar bases de datos
        await init_all_databases()
        
        # Crear procesador
        processor = OpinionProcessor(batch_size=args.batch_size)
        
        # Mostrar estadísticas iniciales
        stats = await processor.obtener_estadisticas()
        print(f"Total de opiniones pendientes: {stats['total_pendientes']}")
        print(f"Modelo utilizado: {stats['modelo_version']}")
        print()
        
        if stats['total_pendientes'] == 0:
            print("✓ No hay opiniones pendientes de análisis")
            return
        
        # Determinar cuántas procesar
        limit = args.limit if args.limit > 0 else stats['total_pendientes']
        
        print(f"Procesando hasta {limit} opiniones...")
        print()
        
        # Procesar
        resultado = await processor.procesar_pendientes(
            limit=limit,
            skip=args.skip
        )
        
        # Mostrar resultados
        print("\n" + "="*80)
        print("RESULTADO DEL ANÁLISIS")
        print("="*80)
        print(f"  Opiniones procesadas: {resultado['procesadas']}")
        print(f"  Actualizaciones exitosas: {resultado['exitosas']}")
        print(f"  Errores: {resultado['errores']}")
        
        if resultado['exitosas'] > 0:
            print(f"\n  Tasa de éxito: {resultado['exitosas'] / resultado['procesadas'] * 100:.1f}%")
        
        print("="*80 + "\n")
    
    except Exception as e:
        logger.error(f"Error en comando analizar: {e}", exc_info=True)
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)
    
    finally:
        await close_all_databases()


async def comando_profesor(args):
    """
    Comando para analizar opiniones de un profesor específico.
    
    Args:
        args: Argumentos de línea de comandos
    """
    print("\n" + "="*80)
    print(f"ANÁLISIS DE SENTIMIENTO - Profesor ID: {args.profesor_id}")
    print("="*80 + "\n")
    
    try:
        # Inicializar bases de datos
        await init_all_databases()
        
        # Crear procesador
        processor = OpinionProcessor(batch_size=args.batch_size)
        
        # Procesar profesor
        resultado = await processor.procesar_por_profesor(
            profesor_id=args.profesor_id,
            limit=args.limit if args.limit > 0 else 1000
        )
        
        # Mostrar resultados
        print("\n" + "="*80)
        print("RESULTADO DEL ANÁLISIS")
        print("="*80)
        print(f"  Profesor ID: {resultado['profesor_id']}")
        print(f"  Opiniones procesadas: {resultado['procesadas']}")
        print(f"  Actualizaciones exitosas: {resultado['exitosas']}")
        print(f"  Errores: {resultado['errores']}")
        
        if resultado['exitosas'] > 0:
            print(f"\n  Tasa de éxito: {resultado['exitosas'] / resultado['procesadas'] * 100:.1f}%")
        
        print("="*80 + "\n")
    
    except Exception as e:
        logger.error(f"Error en comando profesor: {e}", exc_info=True)
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)
    
    finally:
        await close_all_databases()


async def comando_curso(args):
    """
    Comando para analizar opiniones de un curso específico.
    
    Args:
        args: Argumentos de línea de comandos
    """
    print("\n" + "="*80)
    print(f"ANÁLISIS DE SENTIMIENTO - Curso: {args.curso}")
    print("="*80 + "\n")
    
    try:
        # Inicializar bases de datos
        await init_all_databases()
        
        # Crear procesador
        processor = OpinionProcessor(batch_size=args.batch_size)
        
        # Procesar curso
        resultado = await processor.procesar_por_curso(
            curso=args.curso,
            limit=args.limit if args.limit > 0 else 1000
        )
        
        # Mostrar resultados
        print("\n" + "="*80)
        print("RESULTADO DEL ANÁLISIS")
        print("="*80)
        print(f"  Curso: {resultado['curso']}")
        print(f"  Opiniones procesadas: {resultado['procesadas']}")
        print(f"  Actualizaciones exitosas: {resultado['exitosas']}")
        print(f"  Errores: {resultado['errores']}")
        
        if resultado['exitosas'] > 0:
            print(f"\n  Tasa de éxito: {resultado['exitosas'] / resultado['procesadas'] * 100:.1f}%")
        
        print("="*80 + "\n")
    
    except Exception as e:
        logger.error(f"Error en comando curso: {e}", exc_info=True)
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)
    
    finally:
        await close_all_databases()


async def comando_stats(args):
    """
    Comando para mostrar estadísticas de análisis.
    
    Args:
        args: Argumentos de línea de comandos
    """
    print("\n" + "="*80)
    print("ESTADÍSTICAS DE ANÁLISIS DE SENTIMIENTO")
    print("="*80 + "\n")
    
    try:
        # Inicializar bases de datos
        await init_all_databases()
        
        # Crear procesador
        processor = OpinionProcessor()
        
        # Obtener estadísticas
        stats = await processor.obtener_estadisticas()
        
        print(f"Opiniones pendientes de análisis: {stats['total_pendientes']}")
        print(f"Modelo configurado: {stats['modelo_version']}")
        print()
        
        print("="*80 + "\n")
    
    except Exception as e:
        logger.error(f"Error en comando stats: {e}", exc_info=True)
        print(f"\n✗ Error: {e}\n")
        sys.exit(1)
    
    finally:
        await close_all_databases()


# ============================================================================
# CLI PRINCIPAL
# ============================================================================

def main():
    """
    Punto de entrada principal del CLI.
    """
    parser = argparse.ArgumentParser(
        description="SentimentInsightUAM_SA - Análisis de Sentimientos para UAM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  
  # Analizar todas las opiniones pendientes
  python -m src.cli analizar
  
  # Analizar hasta 50 opiniones
  python -m src.cli analizar --limit 50
  
  # Analizar opiniones de un profesor específico
  python -m src.cli profesor --id 123
  
  # Analizar opiniones de un curso
  python -m src.cli curso --name "Estructura de Datos"
  
  # Ver estadísticas
  python -m src.cli stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponibles')
    
    # Comando: analizar
    parser_analizar = subparsers.add_parser(
        'analizar',
        help='Analiza opiniones pendientes de sentimiento general'
    )
    parser_analizar.add_argument(
        '--limit',
        type=int,
        default=-1,
        help='Máximo de opiniones a procesar (-1 para todas)'
    )
    parser_analizar.add_argument(
        '--skip',
        type=int,
        default=0,
        help='Número de opiniones a omitir'
    )
    parser_analizar.add_argument(
        '--batch-size',
        type=int,
        default=8,
        help='Tamaño de batch para procesamiento (default: 8)'
    )
    
    # Comando: profesor
    parser_profesor = subparsers.add_parser(
        'profesor',
        help='Analiza opiniones de un profesor específico'
    )
    parser_profesor.add_argument(
        '--id',
        type=int,
        required=True,
        dest='profesor_id',
        help='ID del profesor en PostgreSQL'
    )
    parser_profesor.add_argument(
        '--limit',
        type=int,
        default=-1,
        help='Máximo de opiniones a procesar (-1 para todas)'
    )
    parser_profesor.add_argument(
        '--batch-size',
        type=int,
        default=8,
        help='Tamaño de batch para procesamiento (default: 8)'
    )
    
    # Comando: curso
    parser_curso = subparsers.add_parser(
        'curso',
        help='Analiza opiniones de un curso específico'
    )
    parser_curso.add_argument(
        '--name',
        type=str,
        required=True,
        dest='curso',
        help='Nombre del curso'
    )
    parser_curso.add_argument(
        '--limit',
        type=int,
        default=-1,
        help='Máximo de opiniones a procesar (-1 para todas)'
    )
    parser_curso.add_argument(
        '--batch-size',
        type=int,
        default=8,
        help='Tamaño de batch para procesamiento (default: 8)'
    )
    
    # Comando: stats
    parser_stats = subparsers.add_parser(
        'stats',
        help='Muestra estadísticas de análisis'
    )
    
    # Parse argumentos
    args = parser.parse_args()
    
    # Ejecutar comando
    if args.comando == 'analizar':
        asyncio.run(comando_analizar(args))
    elif args.comando == 'profesor':
        asyncio.run(comando_profesor(args))
    elif args.comando == 'curso':
        asyncio.run(comando_curso(args))
    elif args.comando == 'stats':
        asyncio.run(comando_stats(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
