"""
Módulo de procesamiento de opiniones para análisis de sentimiento.

Este módulo es el COORDINADOR CENTRAL del flujo de análisis. Orquesta:

1. LECTURA: Obtiene opiniones pendientes desde MongoDB
2. ANÁLISIS DE SENTIMIENTO: Usa BERT (SentimentAnalyzer) para clasificar 
   el sentimiento general (positivo/neutral/negativo)
3. CATEGORIZACIÓN: Usa palabras clave (OpinionCategorizer) para clasificar
   en 3 dimensiones: calidad didáctica, método de evaluación, empatía
4. PERSISTENCIA: Actualiza los resultados en MongoDB

FLUJO DE DATOS:
===============

    MongoDB                    OpinionProcessor                      MongoDB
    ┌──────────┐              ┌──────────────────┐                  ┌──────────┐
    │ opiniones│──lectura────►│                  │                  │ opiniones│
    │ (raw)    │              │  ┌────────────┐  │                  │ (con     │
    └──────────┘              │  │ BERT       │  │──actualización──►│ análisis)│
                              │  │ Sentiment  │  │                  └──────────┘
                              │  └────────────┘  │
                              │  ┌────────────┐  │
                              │  │ Keyword    │  │
                              │  │ Categorizer│  │
                              │  └────────────┘  │
                              └──────────────────┘

Soporta procesamiento en batch para eficiencia con grandes volúmenes.

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
    obtener_todas_las_opiniones,
    contar_todas_las_opiniones,
    actualizar_sentimiento_general,
    actualizar_categorizacion,
    obtener_opiniones_por_profesor,
    obtener_opiniones_por_curso
)
from src.ml import get_analyzer, SentimentAnalyzer
from src.ml.categorizer import get_categorizer, OpinionCategorizer

logger = logging.getLogger(__name__)


class OpinionProcessor:
    """
    Procesador central de opiniones para análisis de sentimiento y categorización.
    
    Esta clase es el orquestador principal que coordina:
    - Lectura de opiniones desde MongoDB
    - Análisis de sentimiento con modelo BERT
    - Categorización en 3 dimensiones con palabras clave
    - Actualización de resultados en MongoDB
    
    ARQUITECTURA:
    =============
    
    OpinionProcessor
          │
          ├── SentimentAnalyzer (BERT)
          │     └── Clasifica: positivo / neutral / negativo
          │
          └── OpinionCategorizer (Keywords)
                └── Clasifica 3 dimensiones:
                      ├── calidad_didactica
                      ├── metodo_evaluacion
                      └── empatia
    
    Attributes:
        batch_size: Número de opiniones a procesar en cada batch
        analyzer: Instancia de SentimentAnalyzer (BERT)
        categorizer: Instancia de OpinionCategorizer (palabras clave)
    
    Example:
        >>> processor = OpinionProcessor(batch_size=16)
        >>> resultado = await processor.procesar_pendientes(limit=100)
        >>> print(f"Procesadas: {resultado['exitosas']}")
    """
    
    def __init__(self, batch_size: int = 10):
        """
        Inicializa el procesador de opiniones.
        
        Args:
            batch_size: Tamaño del batch para procesamiento.
                       Valores mayores = más rápido pero más memoria.
                       Recomendado: 8-16 para CPU, 32-64 para GPU.
        
        Note:
            El analizador y categorizador se inicializan de forma lazy
            (solo cuando se necesitan) para evitar cargar el modelo BERT
            si no se va a usar.
        """
        self.batch_size = batch_size
        self.analyzer: Optional[SentimentAnalyzer] = None
        self.categorizer: Optional[OpinionCategorizer] = None
        
    async def init_analyzer(self) -> None:
        """
        Inicializa los componentes de análisis de forma lazy.
        
        Este método carga:
        1. SentimentAnalyzer: Modelo BERT para sentimiento general
           - Descarga el modelo de HuggingFace si no está en caché
           - Lo carga en memoria (CPU/GPU según configuración)
        
        2. OpinionCategorizer: Categorizador basado en palabras clave
           - Inicialización instantánea (no requiere modelo ML)
        
        TIEMPO DE CARGA:
        ================
        - Primera vez: 30-60 segundos (descarga ~440MB)
        - Siguientes: 5-10 segundos (carga desde caché)
        
        Note:
            Este método es idempotente: llamarlo múltiples veces
            no recarga los modelos si ya están inicializados.
        """
        # =====================================================================
        # Inicializar analizador de sentimiento (BERT)
        # =====================================================================
        if self.analyzer is None:
            # Obtener instancia singleton del analizador
            self.analyzer = get_analyzer()
            logger.info(f"Inicializando analizador con modelo: {self.analyzer.model_name}...")
            
            # Cargar modelo BERT en memoria
            # Esto puede tardar varios segundos la primera vez
            self.analyzer.load_model()
            logger.info(f"✓ Analizador listo ({self.analyzer.model_name})")
        
        # =====================================================================
        # Inicializar categorizador (palabras clave)
        # =====================================================================
        if self.categorizer is None:
            logger.info("Inicializando categorizador...")
            # Obtener instancia singleton del categorizador
            # Esto es instantáneo (no carga modelo ML)
            self.categorizer = get_categorizer()
            logger.info("✓ Categorizador listo")
    
    async def procesar_pendientes(
        self,
        limit: int = 100,
        skip: int = 0,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Procesa opiniones pendientes de análisis.
        
        Este es el método principal para procesamiento masivo. Lee opiniones
        de MongoDB que aún no tienen análisis y les aplica:
        1. Análisis de sentimiento con BERT
        2. Categorización en 3 dimensiones con palabras clave
        
        FLUJO DETALLADO:
        ================
        
        1. Obtener opiniones pendientes de MongoDB
           │
           ▼
        2. Extraer textos (comentarios) en lista
           │
           ▼
        3. Analizar sentimiento en batch (BERT)
           │  - Clasifica: positivo/neutral/negativo
           │  - Calcula confianza y pesos
           ▼
        4. Categorizar en batch (Keywords)
           │  - Evalúa 3 dimensiones
           │  - Detecta palabras clave
           ▼
        5. Actualizar cada opinión en MongoDB
           │  - Guarda sentimiento_general
           │  - Guarda categorizacion
           ▼
        6. Retornar estadísticas
        
        Args:
            limit: Máximo de opiniones a procesar en esta ejecución.
                   Usar valores pequeños (50-100) para pruebas,
                   valores grandes (1000+) para procesamiento masivo.
            skip: Número de opiniones a omitir (para paginación).
                  Útil para continuar un procesamiento interrumpido.
            force: Si True, re-analiza TODAS las opiniones, incluso
                   las que ya tienen análisis. Útil para:
                   - Actualizar con nuevo modelo
                   - Corregir errores previos
        
        Returns:
            Dict con estadísticas del procesamiento:
            {
                "procesadas": int,    # Total de opiniones procesadas
                "exitosas": int,      # Actualizaciones exitosas
                "errores": int,       # Errores durante actualización
                "detalles": [         # Detalle por opinión
                    {
                        "opinion_id": str,
                        "clasificacion": str,
                        "confianza": float,
                        "estado": "exitoso" | "error"
                    }
                ]
            }
        
        Example:
            >>> # Procesar 50 opiniones pendientes
            >>> resultado = await processor.procesar_pendientes(limit=50)
            >>> print(f"Exitosas: {resultado['exitosas']}/{resultado['procesadas']}")
            
            >>> # Re-procesar todas las opiniones (forzar)
            >>> resultado = await processor.procesar_pendientes(limit=1000, force=True)
        """
        # Asegurar que los analizadores están inicializados
        await self.init_analyzer()
        
        # =====================================================================
        # PASO 1: Obtener opiniones de MongoDB
        # =====================================================================
        if force:
            # Modo FORCE: obtener todas las opiniones (ya analizadas o no)
            logger.info(f"[FORCE] Obteniendo hasta {limit} opiniones (todas)...")
            opiniones = await obtener_todas_las_opiniones(
                limit=limit,
                skip=skip
            )
        else:
            # Modo normal: solo opiniones sin análisis previo
            logger.info(f"Obteniendo hasta {limit} opiniones pendientes...")
            opiniones = await obtener_opiniones_pendientes_sentimiento(
                limit=limit,
                skip=skip
            )
        
        # Verificar si hay opiniones para procesar
        if not opiniones:
            logger.info("✓ No hay opiniones pendientes de análisis")
            return {
                "procesadas": 0,
                "exitosas": 0,
                "errores": 0,
                "detalles": []
            }
        
        logger.info(f"Procesando {len(opiniones)} opiniones...")
        
        # =====================================================================
        # PASO 2: Preparar datos para análisis en batch
        # =====================================================================
        # Extraer solo los textos (comentarios) para procesamiento
        textos = [op.get("comentario", "") for op in opiniones]
        # Guardar IDs para actualización posterior
        opinion_ids = [str(op["_id"]) for op in opiniones]
        
        # =====================================================================
        # PASO 3: Análisis de sentimiento en batch (BERT)
        # =====================================================================
        try:
            # analizar_batch procesa múltiples textos eficientemente
            # Retorna lista de SentimentResult con clasificación y confianza
            resultados_sentimiento = self.analyzer.analizar_batch(textos, self.batch_size)
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento batch: {e}")
            return {
                "procesadas": 0,
                "exitosas": 0,
                "errores": len(opiniones),
                "mensaje_error": str(e)
            }
        
        # =====================================================================
        # PASO 4: Categorización en batch (Palabras clave)
        # =====================================================================
        try:
            # categorizar_batch evalúa las 3 dimensiones para cada texto
            # Retorna lista de CategorizacionResult
            resultados_categorizacion = self.categorizer.categorizar_batch(textos)
        except Exception as e:
            logger.error(f"Error en categorización batch: {e}")
            return {
                "procesadas": 0,
                "exitosas": 0,
                "errores": len(opiniones),
                "mensaje_error": str(e)
            }
        
        # =====================================================================
        # PASO 5: Actualizar MongoDB con resultados
        # =====================================================================
        exitosas = 0
        errores = 0
        detalles = []
        
        # Iterar sobre cada opinión con sus resultados
        for opinion_id, resultado_sent, resultado_cat in zip(
            opinion_ids, resultados_sentimiento, resultados_categorizacion
        ):
            try:
                # Actualizar documento con sentimiento general
                # Esto guarda: clasificacion, pesos, confianza, modelo, timestamp
                actualizado_sent = await actualizar_sentimiento_general(
                    opinion_id=opinion_id,
                    clasificacion=resultado_sent.clasificacion,
                    pesos=resultado_sent.pesos,
                    confianza=resultado_sent.confianza,
                    modelo_version=self.analyzer.get_model_version(),
                    tiempo_procesamiento_ms=resultado_sent.tiempo_ms
                )
                
                # Actualizar documento con categorización
                # Esto guarda las 3 dimensiones con valoración y palabras clave
                actualizado_cat = await actualizar_categorizacion(
                    opinion_id=opinion_id,
                    calidad_didactica=resultado_cat.calidad_didactica,
                    metodo_evaluacion=resultado_cat.metodo_evaluacion,
                    empatia=resultado_cat.empatia,
                    modelo_version=self.categorizer.get_version(),
                    tiempo_procesamiento_ms=resultado_cat.tiempo_ms
                )
                
                # Verificar que ambas actualizaciones fueron exitosas
                if actualizado_sent and actualizado_cat:
                    exitosas += 1
                    detalles.append({
                        "opinion_id": opinion_id,
                        "clasificacion": resultado_sent.clasificacion,
                        "confianza": resultado_sent.confianza,
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
        
        # =====================================================================
        # PASO 6: Log y retorno de estadísticas
        # =====================================================================
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
        
        Útil para:
        - Analizar opiniones de un profesor recién agregado
        - Re-procesar opiniones de un profesor específico
        - Generar reportes individuales
        
        FLUJO:
        ======
        1. Obtener todas las opiniones del profesor (por profesor_id)
        2. Filtrar solo las pendientes de análisis
        3. Aplicar análisis de sentimiento + categorización
        4. Actualizar en MongoDB
        
        Args:
            profesor_id: ID del profesor en PostgreSQL (tabla profesores).
                        Este ID se usa para buscar en MongoDB.
            limit: Máximo de opiniones a procesar (default: 100)
        
        Returns:
            Dict con estadísticas:
            {
                "profesor_id": int,
                "procesadas": int,
                "exitosas": int,
                "errores": int
            }
        
        Example:
            >>> # Procesar opiniones del profesor con ID 36
            >>> resultado = await processor.procesar_por_profesor(profesor_id=36)
            >>> print(f"Profesor {resultado['profesor_id']}: {resultado['exitosas']} analizadas")
        """
        await self.init_analyzer()
        
        logger.info(f"Obteniendo opiniones del profesor {profesor_id}...")
        
        # =====================================================================
        # Obtener opiniones del profesor desde MongoDB
        # =====================================================================
        opiniones = await obtener_opiniones_por_profesor(
            profesor_id=profesor_id,
            limit=limit
        )
        
        # =====================================================================
        # Filtrar solo opiniones pendientes de análisis
        # =====================================================================
        # Una opinión está pendiente si:
        # - No tiene sentimiento_general.analizado = True, O
        # - No tiene categorizacion.analizado = True
        opiniones_pendientes = [
            op for op in opiniones
            if (not op.get("sentimiento_general", {}).get("analizado", False) or
                not op.get("categorizacion", {}).get("analizado", False))
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
        
        # =====================================================================
        # Preparar datos y analizar en batch
        # =====================================================================
        textos = [op.get("comentario", "") for op in opiniones_pendientes]
        opinion_ids = [str(op["_id"]) for op in opiniones_pendientes]
        
        # Análisis de sentimiento con BERT
        resultados_sentimiento = self.analyzer.analizar_batch(textos, self.batch_size)
        
        # Análisis de categorización con palabras clave
        resultados_categorizacion = self.categorizer.categorizar_batch(textos)
        
        # =====================================================================
        # Actualizar cada opinión en MongoDB
        # =====================================================================
        exitosas = 0
        errores = 0
        
        for opinion_id, resultado_sent, resultado_cat in zip(
            opinion_ids, resultados_sentimiento, resultados_categorizacion
        ):
            try:
                # Actualizar sentimiento general
                actualizado_sent = await actualizar_sentimiento_general(
                    opinion_id=opinion_id,
                    clasificacion=resultado_sent.clasificacion,
                    pesos=resultado_sent.pesos,
                    confianza=resultado_sent.confianza,
                    modelo_version=self.analyzer.get_model_version(),
                    tiempo_procesamiento_ms=resultado_sent.tiempo_ms
                )
                
                # Actualizar categorización (3 dimensiones)
                actualizado_cat = await actualizar_categorizacion(
                    opinion_id=opinion_id,
                    calidad_didactica=resultado_cat.calidad_didactica,
                    metodo_evaluacion=resultado_cat.metodo_evaluacion,
                    empatia=resultado_cat.empatia,
                    modelo_version=self.categorizer.get_version(),
                    tiempo_procesamiento_ms=resultado_cat.tiempo_ms
                )
                
                if actualizado_sent and actualizado_cat:
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
        Procesa opiniones de un curso/materia específica.
        
        Útil para:
        - Analizar opiniones de una materia nueva
        - Comparar percepción entre diferentes materias
        - Generar reportes por asignatura
        
        BÚSQUEDA:
        =========
        La búsqueda del curso es por coincidencia parcial (regex),
        case-insensitive. Ejemplo:
        - curso="Estructura" matchea "Estructura de Datos", "Estructuras", etc.
        - curso="Base" matchea "Bases de Datos", "Base de Datos I", etc.
        
        Args:
            curso: Nombre o parte del nombre del curso.
                   Se busca como substring case-insensitive.
            limit: Máximo de opiniones a procesar (default: 100)
        
        Returns:
            Dict con estadísticas:
            {
                "curso": str,
                "procesadas": int,
                "exitosas": int,
                "errores": int
            }
        
        Example:
            >>> # Procesar opiniones de cursos que contienen "Datos"
            >>> resultado = await processor.procesar_por_curso(curso="Datos")
            >>> print(f"Curso '{resultado['curso']}': {resultado['exitosas']} analizadas")
        """
        await self.init_analyzer()
        
        logger.info(f"Obteniendo opiniones del curso '{curso}'...")
        
        # =====================================================================
        # Obtener opiniones del curso desde MongoDB
        # =====================================================================
        opiniones = await obtener_opiniones_por_curso(
            curso=curso,
            limit=limit
        )
        
        # =====================================================================
        # Filtrar solo opiniones pendientes
        # =====================================================================
        opiniones_pendientes = [
            op for op in opiniones
            if (not op.get("sentimiento_general", {}).get("analizado", False) or
                not op.get("categorizacion", {}).get("analizado", False))
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
        
        # =====================================================================
        # Preparar y analizar en batch
        # =====================================================================
        textos = [op.get("comentario", "") for op in opiniones_pendientes]
        opinion_ids = [str(op["_id"]) for op in opiniones_pendientes]
        
        # Análisis de sentimiento (BERT)
        resultados_sentimiento = self.analyzer.analizar_batch(textos, self.batch_size)
        
        # Categorización (palabras clave)
        resultados_categorizacion = self.categorizer.categorizar_batch(textos)
        
        # =====================================================================
        # Actualizar MongoDB
        # =====================================================================
        exitosas = 0
        errores = 0
        
        for opinion_id, resultado_sent, resultado_cat in zip(
            opinion_ids, resultados_sentimiento, resultados_categorizacion
        ):
            try:
                # Guardar sentimiento general
                actualizado_sent = await actualizar_sentimiento_general(
                    opinion_id=opinion_id,
                    clasificacion=resultado_sent.clasificacion,
                    pesos=resultado_sent.pesos,
                    confianza=resultado_sent.confianza,
                    modelo_version=self.analyzer.get_model_version(),
                    tiempo_procesamiento_ms=resultado_sent.tiempo_ms
                )
                
                # Guardar categorización
                actualizado_cat = await actualizar_categorizacion(
                    opinion_id=opinion_id,
                    calidad_didactica=resultado_cat.calidad_didactica,
                    metodo_evaluacion=resultado_cat.metodo_evaluacion,
                    empatia=resultado_cat.empatia,
                    modelo_version=self.categorizer.get_version(),
                    tiempo_procesamiento_ms=resultado_cat.tiempo_ms
                )
                
                if actualizado_sent and actualizado_cat:
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
    
    async def obtener_estadisticas(self, force: bool = False) -> Dict[str, Any]:
        """
        Obtiene estadísticas del estado actual de procesamiento.
        
        Útil para:
        - Verificar cuántas opiniones faltan por analizar
        - Monitorear progreso de procesamiento
        - Dashboards y reportes
        
        Args:
            force: Si True, cuenta TODAS las opiniones (no solo pendientes).
                   Útil para saber el total en la base de datos.
        
        Returns:
            Dict con estadísticas:
            {
                "total_pendientes": int,    # Opiniones sin analizar (o total si force=True)
                "modelo_version": str,      # Versión del modelo BERT cargado
                "force": bool               # Indica si se contaron todas
            }
        
        Example:
            >>> # Ver cuántas opiniones faltan
            >>> stats = await processor.obtener_estadisticas()
            >>> print(f"Pendientes: {stats['total_pendientes']}")
            
            >>> # Ver total de opiniones
            >>> stats = await processor.obtener_estadisticas(force=True)
            >>> print(f"Total en BD: {stats['total_pendientes']}")
        """
        if force:
            # Contar todas las opiniones en la colección
            total = await contar_todas_las_opiniones()
        else:
            # Contar solo las que no tienen análisis
            total = await contar_opiniones_pendientes_sentimiento()
        
        return {
            "total_pendientes": total,
            "modelo_version": self.analyzer.get_model_version() if self.analyzer else "No cargado",
            "force": force
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "OpinionProcessor",
]
