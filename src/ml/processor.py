"""
Módulo de procesamiento de opiniones para análisis de sentimiento.

Coordina el flujo completo:
1. Leer opiniones pendientes de MongoDB
2. Analizar sentimiento con BERT
3. Actualizar resultados en MongoDB

Soporta procesamiento batch para eficiencia.

Autor: SentimentInsightUAM Team
Fecha: 2025-11-09
"""

import asyncio
from typing import List, Dict, Any, Optional
import logging

from src.db import get_db_session
from src.db.repository import (
    obtener_opiniones_pendientes_sentimiento,
    contar_opiniones_pendientes_sentimiento,
    actualizar_sentimiento_general,
    obtener_opiniones_por_profesor,
    obtener_opiniones_por_curso
)
from src.ml import get_analyzer, SentimentAnalyzer

logger = logging.getLogger(__name__)


class OpinionProcessor:
    """
    Procesador de opiniones para análisis de sentimiento.
    
    Gestiona el flujo completo de lectura, análisis y actualización.
    """
    
    def __init__(self, batch_size: int = 10):
        """
        Inicializa el procesador.
        
        Args:
            batch_size: Tamaño de batch para procesamiento
        """
        self.batch_size = batch_size
        self.analyzer: Optional[SentimentAnalyzer] = None
        
    async def init_analyzer(self) -> None:
        """
        Inicializa el analizador de sentimiento.
        Carga el modelo BERT en memoria.
        """
        if self.analyzer is None:
            logger.info("Inicializando analizador BERT...")
            self.analyzer = get_analyzer()
            self.analyzer.load_model()
            logger.info("✓ Analizador listo")
    
    async def procesar_pendientes(
        self,
        limit: int = 100,
        skip: int = 0
    ) -> Dict[str, Any]:
        """
        Procesa opiniones pendientes de análisis de sentimiento.
        
        Args:
            limit: Máximo de opiniones a procesar
            skip: Número de opiniones a omitir
        
        Returns:
            Dict con estadísticas del procesamiento
        """
        await self.init_analyzer()
        
        logger.info(f"Obteniendo hasta {limit} opiniones pendientes...")
        
        # Obtener opiniones pendientes
        opiniones = await obtener_opiniones_pendientes_sentimiento(
            limit=limit,
            skip=skip
        )
        
        if not opiniones:
            logger.info("✓ No hay opiniones pendientes de análisis")
            return {
                "procesadas": 0,
                "exitosas": 0,
                "errores": 0,
                "detalles": []
            }
        
        logger.info(f"Procesando {len(opiniones)} opiniones...")
        
        # Extraer textos para análisis en batch
        textos = [op.get("comentario", "") for op in opiniones]
        opinion_ids = [str(op["_id"]) for op in opiniones]
        
        # Analizar en batch
        try:
            resultados = self.analyzer.analizar_batch(textos, self.batch_size)
        except Exception as e:
            logger.error(f"Error en análisis batch: {e}")
            return {
                "procesadas": 0,
                "exitosas": 0,
                "errores": len(opiniones),
                "mensaje_error": str(e)
            }
        
        # Actualizar MongoDB con resultados
        exitosas = 0
        errores = 0
        detalles = []
        
        for opinion_id, resultado in zip(opinion_ids, resultados):
            try:
                actualizado = await actualizar_sentimiento_general(
                    opinion_id=opinion_id,
                    clasificacion=resultado.clasificacion,
                    pesos=resultado.pesos,
                    confianza=resultado.confianza,
                    modelo_version=self.analyzer.get_model_version(),
                    tiempo_procesamiento_ms=resultado.tiempo_ms
                )
                
                if actualizado:
                    exitosas += 1
                    detalles.append({
                        "opinion_id": opinion_id,
                        "clasificacion": resultado.clasificacion,
                        "confianza": resultado.confianza,
                        "estado": "exitoso"
                    })
                else:
                    errores += 1
                    detalles.append({
                        "opinion_id": opinion_id,
                        "estado": "error",
                        "mensaje": "No se pudo actualizar MongoDB"
                    })
            
            except Exception as e:
                errores += 1
                detalles.append({
                    "opinion_id": opinion_id,
                    "estado": "error",
                    "mensaje": str(e)
                })
                logger.error(f"Error al actualizar opinión {opinion_id}: {e}")
        
        logger.info(f"✓ Procesamiento completo: {exitosas} exitosas, {errores} errores")
        
        return {
            "procesadas": len(opiniones),
            "exitosas": exitosas,
            "errores": errores,
            "detalles": detalles
        }
    
    async def procesar_por_profesor(
        self,
        profesor_id: int,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Procesa opiniones de un profesor específico.
        
        Args:
            profesor_id: ID del profesor en PostgreSQL
            limit: Máximo de opiniones a procesar
        
        Returns:
            Dict con estadísticas del procesamiento
        """
        await self.init_analyzer()
        
        logger.info(f"Obteniendo opiniones del profesor {profesor_id}...")
        
        # Obtener opiniones del profesor
        opiniones = await obtener_opiniones_por_profesor(
            profesor_id=profesor_id,
            limit=limit
        )
        
        # Filtrar solo las no analizadas
        opiniones_pendientes = [
            op for op in opiniones
            if not op.get("sentimiento_general", {}).get("analizado", False)
        ]
        
        if not opiniones_pendientes:
            logger.info(f"✓ No hay opiniones pendientes para profesor {profesor_id}")
            return {
                "profesor_id": profesor_id,
                "procesadas": 0,
                "exitosas": 0,
                "errores": 0
            }
        
        logger.info(f"Procesando {len(opiniones_pendientes)} opiniones del profesor...")
        
        # Analizar y actualizar (similar a procesar_pendientes)
        textos = [op.get("comentario", "") for op in opiniones_pendientes]
        opinion_ids = [str(op["_id"]) for op in opiniones_pendientes]
        
        resultados = self.analyzer.analizar_batch(textos, self.batch_size)
        
        exitosas = 0
        errores = 0
        
        for opinion_id, resultado in zip(opinion_ids, resultados):
            try:
                actualizado = await actualizar_sentimiento_general(
                    opinion_id=opinion_id,
                    clasificacion=resultado.clasificacion,
                    pesos=resultado.pesos,
                    confianza=resultado.confianza,
                    modelo_version=self.analyzer.get_model_version(),
                    tiempo_procesamiento_ms=resultado.tiempo_ms
                )
                
                if actualizado:
                    exitosas += 1
                else:
                    errores += 1
            
            except Exception as e:
                errores += 1
                logger.error(f"Error al actualizar opinión {opinion_id}: {e}")
        
        logger.info(f"✓ Profesor {profesor_id}: {exitosas} exitosas, {errores} errores")
        
        return {
            "profesor_id": profesor_id,
            "procesadas": len(opiniones_pendientes),
            "exitosas": exitosas,
            "errores": errores
        }
    
    async def procesar_por_curso(
        self,
        curso: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Procesa opiniones de un curso específico.
        
        Args:
            curso: Nombre del curso
            limit: Máximo de opiniones a procesar
        
        Returns:
            Dict con estadísticas del procesamiento
        """
        await self.init_analyzer()
        
        logger.info(f"Obteniendo opiniones del curso '{curso}'...")
        
        # Obtener opiniones del curso
        opiniones = await obtener_opiniones_por_curso(
            curso=curso,
            limit=limit
        )
        
        # Filtrar solo las no analizadas
        opiniones_pendientes = [
            op for op in opiniones
            if not op.get("sentimiento_general", {}).get("analizado", False)
        ]
        
        if not opiniones_pendientes:
            logger.info(f"✓ No hay opiniones pendientes para curso '{curso}'")
            return {
                "curso": curso,
                "procesadas": 0,
                "exitosas": 0,
                "errores": 0
            }
        
        logger.info(f"Procesando {len(opiniones_pendientes)} opiniones del curso...")
        
        textos = [op.get("comentario", "") for op in opiniones_pendientes]
        opinion_ids = [str(op["_id"]) for op in opiniones_pendientes]
        
        resultados = self.analyzer.analizar_batch(textos, self.batch_size)
        
        exitosas = 0
        errores = 0
        
        for opinion_id, resultado in zip(opinion_ids, resultados):
            try:
                actualizado = await actualizar_sentimiento_general(
                    opinion_id=opinion_id,
                    clasificacion=resultado.clasificacion,
                    pesos=resultado.pesos,
                    confianza=resultado.confianza,
                    modelo_version=self.analyzer.get_model_version(),
                    tiempo_procesamiento_ms=resultado.tiempo_ms
                )
                
                if actualizado:
                    exitosas += 1
                else:
                    errores += 1
            
            except Exception as e:
                errores += 1
                logger.error(f"Error al actualizar opinión {opinion_id}: {e}")
        
        logger.info(f"✓ Curso '{curso}': {exitosas} exitosas, {errores} errores")
        
        return {
            "curso": curso,
            "procesadas": len(opiniones_pendientes),
            "exitosas": exitosas,
            "errores": errores
        }
    
    async def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de opiniones pendientes.
        
        Returns:
            Dict con contadores de opiniones
        """
        total_pendientes = await contar_opiniones_pendientes_sentimiento()
        
        return {
            "total_pendientes": total_pendientes,
            "modelo_version": self.analyzer.get_model_version() if self.analyzer else "No cargado"
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "OpinionProcessor",
]
