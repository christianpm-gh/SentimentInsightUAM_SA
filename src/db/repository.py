"""
Repositorio de consultas para análisis de sentimientos.

Funciones especializadas para:
- Leer opiniones pendientes de análisis
- Actualizar resultados de análisis en MongoDB
- Consultar estadísticas de profesores y cursos

Autor: SentimentInsightUAM Team
Fecha: 2025-11-09
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bson import ObjectId
import logging

from .models import Profesor, Curso, ReseniaMetadata
from . import get_mongo_db

logger = logging.getLogger(__name__)


# ============================================================================
# CONSULTAS POSTGRESQL
# ============================================================================

async def obtener_profesor_por_id(session: AsyncSession, profesor_id: int) -> Optional[Profesor]:
    """
    Obtiene un profesor por su ID.
    
    Args:
        session: Sesión de SQLAlchemy
        profesor_id: ID del profesor
    
    Returns:
        Profesor o None si no existe
    """
    result = await session.execute(
        select(Profesor).where(Profesor.id == profesor_id)
    )
    return result.scalars().first()


async def obtener_profesor_por_slug(session: AsyncSession, slug: str) -> Optional[Profesor]:
    """
    Obtiene un profesor por su slug.
    
    Args:
        session: Sesión de SQLAlchemy
        slug: Slug del profesor
    
    Returns:
        Profesor o None si no existe
    """
    result = await session.execute(
        select(Profesor).where(Profesor.slug == slug)
    )
    return result.scalars().first()


async def obtener_curso_por_id(session: AsyncSession, curso_id: int) -> Optional[Curso]:
    """
    Obtiene un curso por su ID.
    
    Args:
        session: Sesión de SQLAlchemy
        curso_id: ID del curso
    
    Returns:
        Curso o None si no existe
    """
    result = await session.execute(
        select(Curso).where(Curso.id == curso_id)
    )
    return result.scalars().first()


async def obtener_resenias_con_opinion(
    session: AsyncSession,
    profesor_id: Optional[int] = None,
    curso_id: Optional[int] = None,
    limit: int = 100
) -> List[ReseniaMetadata]:
    """
    Obtiene reseñas que tienen opinión textual (comentario).
    
    Args:
        session: Sesión de SQLAlchemy
        profesor_id: Filtrar por profesor (opcional)
        curso_id: Filtrar por curso (opcional)
        limit: Límite de resultados
    
    Returns:
        Lista de ReseniaMetadata
    """
    query = select(ReseniaMetadata).where(
        ReseniaMetadata.tiene_comentario == True
    )
    
    if profesor_id:
        query = query.where(ReseniaMetadata.profesor_id == profesor_id)
    
    if curso_id:
        query = query.where(ReseniaMetadata.curso_id == curso_id)
    
    query = query.limit(limit)
    
    result = await session.execute(query)
    return list(result.scalars().all())


async def contar_opiniones_totales(session: AsyncSession) -> int:
    """
    Cuenta el total de opiniones con comentario.
    
    Args:
        session: Sesión de SQLAlchemy
    
    Returns:
        Número total de opiniones
    """
    result = await session.execute(
        select(func.count(ReseniaMetadata.id)).where(
            ReseniaMetadata.tiene_comentario == True
        )
    )
    return result.scalar()


# ============================================================================
# CONSULTAS MONGODB
# ============================================================================

async def obtener_opiniones_pendientes_sentimiento(
    limit: int = 100,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Obtiene opiniones pendientes de análisis de sentimiento general (Módulo 1).
    
    Args:
        limit: Límite de resultados
        skip: Número de documentos a omitir
    
    Returns:
        Lista de documentos de opiniones
    """
    db = get_mongo_db()
    
    cursor = db.opiniones.find(
        {"sentimiento_general.analizado": False}
    ).skip(skip).limit(limit)
    
    return await cursor.to_list(length=limit)


async def obtener_opiniones_pendientes_categorizacion(
    limit: int = 100,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Obtiene opiniones pendientes de categorización (Módulo 2).
    
    Args:
        limit: Límite de resultados
        skip: Número de documentos a omitir
    
    Returns:
        Lista de documentos de opiniones
    """
    db = get_mongo_db()
    
    cursor = db.opiniones.find(
        {"categorizacion.analizado": False}
    ).skip(skip).limit(limit)
    
    return await cursor.to_list(length=limit)


async def obtener_opinion_por_id(opinion_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene una opinión por su ObjectId.
    
    Args:
        opinion_id: String del ObjectId de MongoDB
    
    Returns:
        Documento de opinión o None
    """
    db = get_mongo_db()
    
    try:
        return await db.opiniones.find_one({"_id": ObjectId(opinion_id)})
    except Exception as e:
        logger.error(f"Error al obtener opinión {opinion_id}: {e}")
        return None


async def obtener_opiniones_por_profesor(
    profesor_id: int,
    limit: int = 100,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Obtiene todas las opiniones de un profesor.
    
    Args:
        profesor_id: ID del profesor en PostgreSQL
        limit: Límite de resultados
        skip: Número de documentos a omitir
    
    Returns:
        Lista de documentos de opiniones
    """
    db = get_mongo_db()
    
    cursor = db.opiniones.find(
        {"profesor_id": profesor_id}
    ).skip(skip).limit(limit)
    
    return await cursor.to_list(length=limit)


async def obtener_opiniones_por_curso(
    curso: str,
    limit: int = 100,
    skip: int = 0
) -> List[Dict[str, Any]]:
    """
    Obtiene opiniones filtradas por nombre de curso.
    
    Args:
        curso: Nombre del curso
        limit: Límite de resultados
        skip: Número de documentos a omitir
    
    Returns:
        Lista de documentos de opiniones
    """
    db = get_mongo_db()
    
    cursor = db.opiniones.find(
        {"curso": {"$regex": curso, "$options": "i"}}
    ).skip(skip).limit(limit)
    
    return await cursor.to_list(length=limit)


async def contar_opiniones_pendientes_sentimiento() -> int:
    """
    Cuenta opiniones pendientes de análisis de sentimiento general.
    
    Returns:
        Número de opiniones pendientes
    """
    db = get_mongo_db()
    return await db.opiniones.count_documents(
        {"sentimiento_general.analizado": False}
    )


async def contar_opiniones_pendientes_categorizacion() -> int:
    """
    Cuenta opiniones pendientes de categorización.
    
    Returns:
        Número de opiniones pendientes
    """
    db = get_mongo_db()
    return await db.opiniones.count_documents(
        {"categorizacion.analizado": False}
    )


# ============================================================================
# ACTUALIZACIÓN DE ANÁLISIS EN MONGODB
# ============================================================================

async def actualizar_sentimiento_general(
    opinion_id: str,
    clasificacion: str,
    pesos: Dict[str, float],
    confianza: float,
    modelo_version: str,
    tiempo_procesamiento_ms: int
) -> bool:
    """
    Actualiza el campo sentimiento_general de una opinión.
    
    Args:
        opinion_id: String del ObjectId
        clasificacion: positivo, neutral, negativo
        pesos: Diccionario con positivo, negativo, neutro
        confianza: Confianza de la clasificación (0 a 1)
        modelo_version: Versión del modelo usado
        tiempo_procesamiento_ms: Tiempo de procesamiento
    
    Returns:
        True si actualización exitosa
    """
    db = get_mongo_db()
    
    try:
        result = await db.opiniones.update_one(
            {"_id": ObjectId(opinion_id)},
            {"$set": {
                "sentimiento_general": {
                    "analizado": True,
                    "clasificacion": clasificacion,
                    "pesos": pesos,
                    "confianza": confianza,
                    "modelo_version": modelo_version,
                    "fecha_analisis": datetime.utcnow(),
                    "tiempo_procesamiento_ms": tiempo_procesamiento_ms
                }
            }}
        )
        
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Error al actualizar sentimiento de opinión {opinion_id}: {e}")
        return False


async def actualizar_categorizacion(
    opinion_id: str,
    calidad_didactica: Dict[str, Any],
    metodo_evaluacion: Dict[str, Any],
    empatia: Dict[str, Any],
    modelo_version: str,
    tiempo_procesamiento_ms: int
) -> bool:
    """
    Actualiza el campo categorizacion de una opinión (Módulo 2).
    
    Args:
        opinion_id: String del ObjectId
        calidad_didactica: Dict con valoracion, confianza, palabras_clave
        metodo_evaluacion: Dict con valoracion, confianza, palabras_clave
        empatia: Dict con valoracion, confianza, palabras_clave
        modelo_version: Versión del modelo usado
        tiempo_procesamiento_ms: Tiempo de procesamiento
    
    Returns:
        True si actualización exitosa
    """
    db = get_mongo_db()
    
    try:
        result = await db.opiniones.update_one(
            {"_id": ObjectId(opinion_id)},
            {"$set": {
                "categorizacion": {
                    "analizado": True,
                    "calidad_didactica": calidad_didactica,
                    "metodo_evaluacion": metodo_evaluacion,
                    "empatia": empatia,
                    "modelo_version": modelo_version,
                    "fecha_analisis": datetime.utcnow(),
                    "tiempo_procesamiento_ms": tiempo_procesamiento_ms
                }
            }}
        )
        
        return result.modified_count > 0
    
    except Exception as e:
        logger.error(f"Error al actualizar categorización de opinión {opinion_id}: {e}")
        return False


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "obtener_profesor_por_id",
    "obtener_profesor_por_slug",
    "obtener_curso_por_id",
    "obtener_resenias_con_opinion",
    "contar_opiniones_totales",
    "obtener_opiniones_pendientes_sentimiento",
    "obtener_opiniones_pendientes_categorizacion",
    "obtener_opinion_por_id",
    "obtener_opiniones_por_profesor",
    "obtener_opiniones_por_curso",
    "contar_opiniones_pendientes_sentimiento",
    "contar_opiniones_pendientes_categorizacion",
    "actualizar_sentimiento_general",
    "actualizar_categorizacion",
]
