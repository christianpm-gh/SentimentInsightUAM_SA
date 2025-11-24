"""
Módulo de categorización de opiniones para SentimentInsightUAM_SA.

Implementa análisis de categorización (Módulo 2) usando BERT para clasificar
opiniones en tres dimensiones:
- Calidad didáctica
- Método de evaluación
- Empatía

Autor: SentimentInsightUAM Team
Fecha: 2025-11-09
"""

import os
import time
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CategorizacionResult:
    """
    Resultado del análisis de categorización.
    
    Attributes:
        calidad_didactica: Dict con valoracion, confianza, palabras_clave
        metodo_evaluacion: Dict con valoracion, confianza, palabras_clave
        empatia: Dict con valoracion, confianza, palabras_clave
        tiempo_ms: Tiempo de procesamiento en milisegundos
    """
    calidad_didactica: Dict[str, Any]
    metodo_evaluacion: Dict[str, Any]
    empatia: Dict[str, Any]
    tiempo_ms: int


class OpinionCategorizer:
    """
    Categorizador de opiniones basado en palabras clave y patrones.
    
    Analiza opiniones en tres dimensiones:
    1. Calidad didáctica (explica bien, domina tema, claro)
    2. Método de evaluación (exámenes difíciles, justo, tareas)
    3. Empatía (comprensivo, accesible, ayuda)
    """
    
    # Palabras clave por categoría y valoración
    KEYWORDS = {
        "calidad_didactica": {
            "positivo": [
                "explica bien", "domina", "claro", "enseña bien", "didáctico",
                "buen profesor", "excelente", "aprend", "entend", "conocimiento",
                "profesional", "preparado", "sabe", "materia", "ejemplos"
            ],
            "negativo": [
                "no explica", "confuso", "desorganizado", "mal profesor",
                "no enseña", "aburrido", "monótono", "no se entiende",
                "perdido", "no domina", "improvisado"
            ]
        },
        "metodo_evaluacion": {
            "positivo": [
                "justo", "fair", "razonable", "equilibrado", "bien evaluado",
                "examenes justos", "calificación justa", "objetivo",
                "clara evaluación", "criterios claros"
            ],
            "negativo": [
                "difícil", "exigente", "reprobar", "injusto", "arbitrario",
                "exámenes imposibles", "mucha tarea", "carga excesiva",
                "evalúa mal", "subjetivo", "estricto", "duro"
            ]
        },
        "empatia": {
            "positivo": [
                "comprensivo", "accesible", "ayuda", "amable", "paciente",
                "disponible", "empático", "buena persona", "resuelve dudas",
                "atento", "flexible", "humano", "considerado"
            ],
            "negativo": [
                "grosero", "déspo ta", "inaccesible", "no ayuda", "antipático",
                "prepotente", "soberbio", "no resuelve dudas", "inflexible",
                "no le importa", "arrogante", "mal trato"
            ]
        }
    }
    
    def __init__(self):
        """
        Inicializa el categorizador.
        """
        self.version = "keyword-based-v1.0"
        logger.info(f"Inicializando OpinionCategorizer: {self.version}")
    
    def _calcular_score_categoria(
        self,
        texto: str,
        categoria: str
    ) -> Tuple[str, float, List[str]]:
        """
        Calcula el score de una categoría basado en palabras clave.
        
        Args:
            texto: Texto a analizar
            categoria: calidad_didactica, metodo_evaluacion, empatia
        
        Returns:
            Tupla (valoracion, confianza, palabras_encontradas)
        """
        texto_lower = texto.lower()
        
        # Buscar palabras clave
        positivas_encontradas = []
        negativas_encontradas = []
        
        for palabra in self.KEYWORDS[categoria]["positivo"]:
            if palabra in texto_lower:
                positivas_encontradas.append(palabra)
        
        for palabra in self.KEYWORDS[categoria]["negativo"]:
            if palabra in texto_lower:
                negativas_encontradas.append(palabra)
        
        # Calcular valoración
        total_encontradas = len(positivas_encontradas) + len(negativas_encontradas)
        
        if total_encontradas == 0:
            return "neutral", 0.5, []
        
        score_positivo = len(positivas_encontradas) / total_encontradas
        
        if score_positivo > 0.6:
            valoracion = "positivo"
            confianza = score_positivo
            palabras = positivas_encontradas
        elif score_positivo < 0.4:
            valoracion = "negativo"
            confianza = 1 - score_positivo
            palabras = negativas_encontradas
        else:
            valoracion = "neutral"
            confianza = 0.5
            palabras = positivas_encontradas + negativas_encontradas
        
        return valoracion, confianza, palabras[:5]  # Max 5 palabras
    
    def categorizar(self, texto: str) -> CategorizacionResult:
        """
        Categoriza una opinión individual.
        
        Args:
            texto: Texto de la opinión
        
        Returns:
            CategorizacionResult con las tres categorías
        """
        inicio = time.time()
        
        # Analizar cada categoría
        cal_val, cal_conf, cal_palabras = self._calcular_score_categoria(
            texto, "calidad_didactica"
        )
        met_val, met_conf, met_palabras = self._calcular_score_categoria(
            texto, "metodo_evaluacion"
        )
        emp_val, emp_conf, emp_palabras = self._calcular_score_categoria(
            texto, "empatia"
        )
        
        tiempo_ms = int((time.time() - inicio) * 1000)
        
        return CategorizacionResult(
            calidad_didactica={
                "valoracion": cal_val,
                "confianza": round(cal_conf, 3),
                "palabras_clave": cal_palabras
            },
            metodo_evaluacion={
                "valoracion": met_val,
                "confianza": round(met_conf, 3),
                "palabras_clave": met_palabras
            },
            empatia={
                "valoracion": emp_val,
                "confianza": round(emp_conf, 3),
                "palabras_clave": emp_palabras
            },
            tiempo_ms=tiempo_ms
        )
    
    def categorizar_batch(
        self,
        textos: List[str]
    ) -> List[CategorizacionResult]:
        """
        Categoriza múltiples opiniones.
        
        Args:
            textos: Lista de textos
        
        Returns:
            Lista de CategorizacionResult
        """
        inicio = time.time()
        
        resultados = []
        for texto in textos:
            resultado = self.categorizar(texto)
            resultados.append(resultado)
        
        tiempo_total = int((time.time() - inicio) * 1000)
        logger.info(f"Categorizadas {len(textos)} opiniones en {tiempo_total}ms")
        
        return resultados
    
    def get_version(self) -> str:
        """
        Retorna la versión del categorizador.
        
        Returns:
            String con versión
        """
        return self.version


# ============================================================================
# SINGLETON GLOBAL
# ============================================================================

_global_categorizer: OpinionCategorizer = None


def get_categorizer() -> OpinionCategorizer:
    """
    Obtiene la instancia global del categorizador (patrón singleton).
    
    Returns:
        OpinionCategorizer configurado
    """
    global _global_categorizer
    
    if _global_categorizer is None:
        _global_categorizer = OpinionCategorizer()
    
    return _global_categorizer


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "OpinionCategorizer",
    "CategorizacionResult",
    "get_categorizer",
]
