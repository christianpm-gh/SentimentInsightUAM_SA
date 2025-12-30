"""
Módulo de categorización de opiniones para SentimentInsightUAM_SA.

Implementa análisis de categorización basado en PALABRAS CLAVE (NO usa ML/BERT)
para clasificar opiniones en tres dimensiones:
- Calidad didáctica: dominio del tema, claridad, metodología de enseñanza
- Método de evaluación: justicia, dificultad, carga de trabajo
- Empatía: trato, accesibilidad, apoyo al estudiante

NOTA: El modelo Robertuito está en caché pero NO se usa actualmente.
      Esta implementación usa detección de patrones léxicos.

Versión: keyword-based-v1.0
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
                # Explicación / claridad
                "explica bien",
                "explica muy bien",
                "explica excelente",
                "explica claro",
                "explica con claridad",
                "explica de forma clara",
                "claro para explicar",
                "clases claras",
                "clase clara",
                "muy claro",
                "super claro",
                "todo claro",
                "deja todo claro",
                "no deja dudas (positiva)",  # ojo: esto se matchea con "no deja dudas"
                # Dominio del tema
                "domina el tema",
                "domina la materia",
                "domina bastante",
                "se nota que sabe",
                "se nota que domina",
                "gran dominio",
                "mucho conocimiento",
                "conocimiento profundo",
                "muy preparado",
                "bien preparado",
                "super preparado",
                "profesor preparado",
                "profesora preparada",
                "preparado en la materia",
                "sabe mucho",
                "sabe bastante",
                "sabe lo que hace",
                "controla el tema",
                # Didáctica / métodos de enseñanza
                "enseña bien",
                "didáctico",
                "muy didáctico",
                "didactico",           # sin tilde
                "buen profesor",
                "buena profesora",
                "excelente profesor",
                "excelente profesora",
                "excelente docente",
                "muy buen maestro",
                "muy buena maestra",
                "usa buenos ejemplos",
                "pone buenos ejemplos",
                "ejemplos claros",
                "ejemplos sencillos",
                "ejemplos prácticos",
                "usa ejercicios",
                "resuelve ejercicios",
                "explica paso a paso",
                "va paso a paso",
                # Estructura de clase
                "clases bien estructuradas",
                "clase bien estructurada",
                "organizado en clase",
                "organizada en clase",
                "sigue un orden",
                "buen manejo del tiempo",
                "buen ritmo de clase",
                "ritmo adecuado",
                # Resultado de aprendizaje
                "aprendí mucho",
                "aprendi mucho",
                "aprendí bastante",
                "aprendi bastante",
                "aprendes demasiado",
                "aprendí con él",
                "aprendi con el",
                "aprendí con ella",
                "se aprende bien",
                "se aprende mucho",
                "entendí todo",
                "entiendes todo",
                "se entiende todo",
                "mejoré bastante",
                "mejoré mucho",
                # Profesionalismo académico
                "muy profesional",
                "profesional en su trabajo",
                "responsable con la clase",
                "puntual con la clase",
                "llega puntual",
            ],
            "negativo": [
                # Falta de explicación
                "no explica",
                "no sabe explicar",
                "explica mal",
                "explica muy mal",
                "no explica bien",
                "explica rápido y mal",
                "explica todo rápido",
                "va muy rápido",
                "va demasiado rápido",
                "explica encima del pizarrón",
                "solo lee diapositivas",
                "solo lee las diapositivas",
                "solo dicta",
                "solo escribe",
                # Confusión / desorden
                "confuso",
                "muy confuso",
                "clases confusas",
                "desorganizado",
                "desorganizada",
                "desordenado",
                "desordenada",
                "mal profesor",
                "mala profesora",
                "pésimo profesor",
                "pesimo profesor",
                "pésima profesora",
                "pesima profesora",
                "no enseña",
                "no se entiende",
                "no se le entiende",
                "no se entiende nada",
                "no se entiende lo que dice",
                "te pierdes en la clase",
                "uno se pierde",
                "me perdí en la clase",
                "no domina el tema",
                "no domina la materia",
                "se equivoca mucho",
                "se la pasa corrigiendo",
                # Aburrimiento / poca dinámica
                "aburrido",
                "aburrida",
                "muy aburrido",
                "muy aburrida",
                "monótono",
                "monotono",
                "monótona",
                "monotona",
                "clases pesadas",
                "clase pesada",
                # Falta de preparación
                "improvisado",
                "improvisada",
                "improvisa la clase",
                "no prepara la clase",
                "llega sin preparar",
                "no sabe la materia",
                "no maneja el tema",
                # Mala organización de contenidos
                "salta muchos temas",
                "se salta temas",
                "mezcla temas",
                "no sigue el temario",
                "no sigue el programa",
                "no respeta el programa",
            ],
        },
        "metodo_evaluacion": {
            "positivo": [
                # Justicia / equilibrio
                "justo",
                "muy justo",
                "justa",
                "muy justa",
                "bastante justo",
                "califica justo",
                "califica justo",
                "calificación justa",
                "calificacion justa",
                "exámenes justos",
                "examenes justos",
                "evalúa justo",
                "evalua justo",
                "evalúa de forma justa",
                "evalua de forma justa",
                "fair",
                "razonable",
                "muy razonable",
                "equilibrado",
                "equilibrada",
                "bien evaluado",
                "bien evaluada",
                "objetivo",
                "objetiva",
                "criterios claros",
                "criterios de evaluación claros",
                "criterios de evaluacion claros",
                "rubrica clara",
                "rúbrica clara",
                # Transparencia
                "explica cómo evalúa",
                "explica como evalua",
                "explica la forma de evaluar",
                "deja claro cómo califica",
                "deja claro como califica",
                "todo bien especificado",
                "publica rubricas",
                "publica rúbricas",
                # Oportunidades / mejoras
                "da oportunidad",
                "da oportunidades",
                "deja recuperar",
                "deja extraordinario",
                "permite extraordinarios",
                "acepta trabajos extra",
                "da puntos extra",
                "sube puntos",
                "sube la calificación",
                "sube la calificacion",
                "permite reposición",
                "permite reposicion",
                # Carga razonable
                "mucha práctica pero justo",
                "mucha practica pero justo",
                "tareas razonables",
                "poca tarea pero efectiva",
                "proyectos razonables",
                "exámenes acordes",
                "examenes acordes",
                "evalúa lo que ve en clase",
                "evalua lo que ve en clase",
                "solo toma lo visto en clase",
            ],
            "negativo": [
                # Dificultad / dureza
                "difícil",
                "dificil",
                "muy difícil",
                "muy dificil",
                "exigente",
                "muy exigente",
                "demasiado exigente",
                "exámenes imposibles",
                "examenes imposibles",
                "exámenes muy difíciles",
                "examenes muy dificiles",
                "preguntas rebuscadas",
                "preguntas trampas",
                "preguntas trampa",
                "reprobar",
                "reprobé a muchos",
                "reprobe a muchos",
                "reprobados masivos",
                "reprobados masivos",
                # Injusticia / arbitrariedad
                "injusto",
                "injusta",
                "muy injusto",
                "muy injusta",
                "evalúa mal",
                "evalua mal",
                "califica mal",
                "califica bajo",
                "califica muy bajo",
                "calificación arbitraria",
                "calificacion arbitraria",
                "criterios arbitrarios",
                "criterios poco claros",
                "no explica cómo evalúa",
                "no explica como evalua",
                "no explica los criterios",
                "no deja claro cómo califica",
                "no deja claro como califica",
                "subjetivo",
                "subjetiva",
                "muy subjetivo",
                "muy subjetiva",
                "caprichoso",
                "caprichosa",
                # Carga de trabajo
                "mucha tarea",
                "demasiada tarea",
                "exceso de tarea",
                "carga excesiva",
                "carga de trabajo excesiva",
                "muchos proyectos",
                "proyectos innecesarios",
                "muchos trabajos",
                "trabajos innecesarios",
                "tareas sin sentido",
                "tarea sin sentido",
                # Desfase con lo visto en clase
                "no evalúa lo que ve en clase",
                "no evalua lo que ve en clase",
                "exámenes de cosas que no vimos",
                "examenes de cosas que no vimos",
                "pregunta cosas que no explicó",
                "pregunta cosas que no explico",
                "toma temas que no vimos",
                # Falta de feedback
                "no da retroalimentación",
                "no da retroalimentacion",
                "no explica las calificaciones",
                "no entrega resultados a tiempo",
                "se tarda en calificar",
                "tarda mucho en calificar",
            ],
        },
        "empatia": {
            "positivo": [
                # Trato humano
                "comprensivo",
                "comprensiva",
                "muy comprensivo",
                "muy comprensiva",
                "accesible",
                "muy accesible",
                "amable",
                "muy amable",
                "buena onda",
                "muy buena onda",
                "relajado",
                "relajada",
                "alivianado",
                "alivianada",
                "buena persona",
                "excelente persona",
                "humano",
                "muy humano",
                "empático",
                "empática",
                "empatico",
                "empatica",
                "considerado",
                "considerada",
                "respetuoso",
                "respetuosa",
                "trato amable",
                "trato humano",
                # Apoyo al estudiante
                "ayuda",
                "siempre ayuda",
                "ayuda mucho",
                "apoya a los alumnos",
                "apoya a sus alumnos",
                "apoya bastante",
                "apoya cuando puede",
                "te apoya",
                "da seguimiento",
                "se preocupa por sus alumnos",
                "se preocupa por los alumnos",
                "se interesa por el alumno",
                "se interesa por los estudiantes",
                "resuelve dudas",
                "resuelve todas las dudas",
                "respuesta rápida",
                "responde rápido",
                "responde rapido",
                "responde correos",
                "responde mensajes",
                # Flexibilidad / empatía en evaluación
                "flexible",
                "muy flexible",
                "flexible con entregas",
                "flexible con fechas",
                "da chance",
                "da chance con tareas",
                "da prórrogas",
                "da prorrogas",
                "da oportunidad de entregar",
                "entendió mi situación",
                "entendio mi situacion",
                "entiende las situaciones",
                "entiende que trabajamos",
                "entiende que trabajas",
                # Disponibilidad
                "disponible",
                "muy disponible",
                "atiende en asesorías",
                "atiende en asesorias",
                "da asesorías",
                "da asesorias",
                "horario de asesoría",
                "horario de asesoria",
                "responde en clase",
                "escucha al alumno",
                "escucha a los alumnos",
            ],
            "negativo": [
                # Mal trato
                "grosero",
                "grosera",
                "muy grosero",
                "muy grosera",
                "déspota",
                "despota",
                "déspota con los alumnos",
                "despota con los alumnos",
                "mal trato",
                "maltrato",
                "trata mal",
                "trata muy mal",
                "antipático",
                "antipatica",
                "antipático",
                "antipática",
                "prepotente",
                "muy prepotente",
                "soberbio",
                "soberbia",
                "arrogante",
                "arrogante con los alumnos",
                "pesado",
                "pesada",
                "muy pesado",
                "muy pesada",
                "mamón con los alumnos",
                "mamona con los alumnos",
                # Falta de apoyo
                "no ayuda",
                "nunca ayuda",
                "no apoya",
                "no apoya a los alumnos",
                "no resuelve dudas",
                "no responde dudas",
                "ignora las dudas",
                "ignora a los alumnos",
                "no responde correos",
                "no responde mensajes",
                "no contesta correos",
                "no contesta mensajes",
                # Falta de empatía / rigidez
                "inflexible",
                "muy inflexible",
                "no da prórrogas",
                "no da prorrogas",
                "no da oportunidad",
                "no da segundas oportunidades",
                "no entiende las situaciones",
                "no entiende que trabajamos",
                "no entiende que trabajas",
                "no le importa el alumno",
                "no le importan los alumnos",
                "le da igual el alumno",
                "le da igual la clase",
                # Indiferencia / distancia
                "inaccesible",
                "muy inaccesible",
                "casi no se le encuentra",
                "no está disponible",
                "no esta disponible",
                "no atiende asesorías",
                "no atiende asesorias",
                "no escucha al alumno",
                "no escucha a los alumnos",
                "se burla de los alumnos",
                "hace comentarios hirientes",
            ],
        },
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
        
        ALGORITMO:
        ==========
        1. Convierte el texto a minúsculas para búsqueda case-insensitive
        2. Busca coincidencias de substrings del diccionario KEYWORDS
        3. Cuenta palabras positivas y negativas encontradas
        4. Calcula proporción: score = positivas / (positivas + negativas)
        5. Clasifica según umbrales:
           - score > 0.6  → "positivo" (mayoría positivas)
           - score < 0.4  → "negativo" (mayoría negativas)
           - 0.4 <= score <= 0.6 → "neutral" (equilibrado)
        
        LIMITACIONES:
        - No detecta negaciones ("no explica bien" matchea "explica bien")
        - No considera contexto semántico
        - Palabras más largas pueden contener palabras más cortas
        
        Args:
            texto: Texto a analizar (opinión del estudiante)
            categoria: Una de: calidad_didactica, metodo_evaluacion, empatia
        
        Returns:
            Tupla (valoracion, confianza, palabras_encontradas)
            - valoracion: "positivo", "negativo", o "neutral"
            - confianza: float entre 0.0 y 1.0
            - palabras_encontradas: lista de hasta 5 keywords detectadas
        """
        # =====================================================================
        # PASO 1: Normalizar texto a minúsculas
        # =====================================================================
        # Esto permite búsqueda case-insensitive
        # Ejemplo: "Explica BIEN" → "explica bien"
        texto_lower = texto.lower()
        
        # =====================================================================
        # PASO 2: Buscar palabras clave en el texto
        # =====================================================================
        # Recorremos cada palabra/frase del diccionario y verificamos
        # si está contenida como substring en el texto
        positivas_encontradas = []
        negativas_encontradas = []
        
        # Buscar keywords positivas
        # Ejemplo: si texto = "explica muy bien y domina el tema"
        #          y KEYWORDS tiene "explica muy bien", "domina el tema"
        #          → positivas_encontradas = ["explica muy bien", "domina el tema"]
        for palabra in self.KEYWORDS[categoria]["positivo"]:
            if palabra in texto_lower:
                positivas_encontradas.append(palabra)
        
        # Buscar keywords negativas
        # Ejemplo: si texto = "no explica y es muy confuso"
        #          y KEYWORDS tiene "no explica", "muy confuso"
        #          → negativas_encontradas = ["no explica", "muy confuso"]
        for palabra in self.KEYWORDS[categoria]["negativo"]:
            if palabra in texto_lower:
                negativas_encontradas.append(palabra)
        
        # =====================================================================
        # PASO 3: Calcular valoración basada en proporción
        # =====================================================================
        total_encontradas = len(positivas_encontradas) + len(negativas_encontradas)
        
        # CASO ESPECIAL: Sin palabras clave detectadas
        # Si no encontramos ninguna keyword, asumimos neutral con confianza 0.5
        # Esto significa que la opinión no habla de esta dimensión
        if total_encontradas == 0:
            return "neutral", 0.5, []
        
        # =====================================================================
        # PASO 4: Calcular score de positividad
        # =====================================================================
        # score_positivo = proporción de keywords positivas sobre el total
        # 
        # Ejemplos:
        #   - 3 positivas, 0 negativas → score = 3/3 = 1.0 (100% positivo)
        #   - 2 positivas, 2 negativas → score = 2/4 = 0.5 (50% equilibrado)
        #   - 1 positiva, 3 negativas → score = 1/4 = 0.25 (25% → mayormente negativo)
        score_positivo = len(positivas_encontradas) / total_encontradas
        
        # =====================================================================
        # PASO 5: Clasificar según umbrales
        # =====================================================================
        # 
        #  NEGATIVO          NEUTRAL           POSITIVO
        #  ◄────────────────┼─────────────────┼────────────────►
        #  0.0             0.4               0.6              1.0
        #
        # - Si score > 0.6: Mayoría de keywords son positivas → POSITIVO
        # - Si score < 0.4: Mayoría de keywords son negativas → NEGATIVO  
        # - Si 0.4 <= score <= 0.6: Equilibrado → NEUTRAL
        #
        if score_positivo > 0.6:
            # CASO POSITIVO: más del 60% de keywords son positivas
            # Confianza = score_positivo (mientras más alto, más confianza)
            # Ejemplo: score=0.8 → confianza=0.8
            valoracion = "positivo"
            confianza = score_positivo
            palabras = positivas_encontradas
            
        elif score_positivo < 0.4:
            # CASO NEGATIVO: menos del 40% son positivas (más del 60% negativas)
            # Confianza = 1 - score_positivo = proporción de negativas
            # Ejemplo: score=0.2 → confianza=0.8 (80% negativas)
            valoracion = "negativo"
            confianza = 1 - score_positivo
            palabras = negativas_encontradas
            
        else:
            # CASO NEUTRAL: entre 40% y 60% positivas (equilibrado)
            # Confianza fija de 0.5 (incertidumbre máxima)
            # Retornamos ambas listas de palabras como evidencia
            valoracion = "neutral"
            confianza = 0.5
            palabras = positivas_encontradas + negativas_encontradas
        
        # Retornar máximo 5 palabras para no saturar la respuesta
        return valoracion, confianza, palabras[:5]
    
    def categorizar(self, texto: str) -> CategorizacionResult:
        """
        Categoriza una opinión individual en las 3 dimensiones.
        
        FLUJO COMPLETO:
        ===============
        
        Entrada: "Muy buen profesor, domina la materia pero es muy exigente"
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │ _calcular_score_categoria(texto, "calidad_didactica")           │
        │   Keywords encontradas: ["buen profesor", "domina la materia"]  │
        │   Score: 2 positivas / 2 total = 1.0                            │
        │   Resultado: ("positivo", 1.0, ["buen profesor", ...])          │
        └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │ _calcular_score_categoria(texto, "metodo_evaluacion")           │
        │   Keywords encontradas: ["muy exigente"]                        │
        │   Score: 0 positivas / 1 total = 0.0                            │
        │   Resultado: ("negativo", 1.0, ["muy exigente"])                │
        └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │ _calcular_score_categoria(texto, "empatia")                     │
        │   Keywords encontradas: []                                      │
        │   Score: 0 / 0 = undefined → neutral                            │
        │   Resultado: ("neutral", 0.5, [])                               │
        └─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌─────────────────────────────────────────────────────────────────┐
        │ CategorizacionResult:                                           │
        │   calidad_didactica: {valoracion: "positivo", confianza: 1.0}   │
        │   metodo_evaluacion: {valoracion: "negativo", confianza: 1.0}   │
        │   empatia: {valoracion: "neutral", confianza: 0.5}              │
        └─────────────────────────────────────────────────────────────────┘
        
        Args:
            texto: Texto de la opinión a categorizar
        
        Returns:
            CategorizacionResult con valoración para cada una de las 3 dimensiones:
            - calidad_didactica: cómo enseña, dominio del tema, claridad
            - metodo_evaluacion: justicia, dificultad, carga de trabajo
            - empatia: trato humano, accesibilidad, apoyo
        """
        # Iniciar cronómetro para medir tiempo de procesamiento
        inicio = time.time()
        
        # =====================================================================
        # Analizar cada una de las 3 dimensiones de forma independiente
        # =====================================================================
        
        # DIMENSIÓN 1: Calidad Didáctica
        # ¿El profesor explica bien? ¿Domina el tema? ¿Es claro?
        cal_val, cal_conf, cal_palabras = self._calcular_score_categoria(
            texto, "calidad_didactica"
        )
        
        # DIMENSIÓN 2: Método de Evaluación
        # ¿Es justo? ¿Los exámenes son difíciles? ¿Hay mucha tarea?
        met_val, met_conf, met_palabras = self._calcular_score_categoria(
            texto, "metodo_evaluacion"
        )
        
        # DIMENSIÓN 3: Empatía
        # ¿Es accesible? ¿Ayuda a los alumnos? ¿Es comprensivo?
        emp_val, emp_conf, emp_palabras = self._calcular_score_categoria(
            texto, "empatia"
        )
        
        # Calcular tiempo total de procesamiento en milisegundos
        tiempo_ms = int((time.time() - inicio) * 1000)
        
        # =====================================================================
        # Construir y retornar resultado estructurado
        # =====================================================================
        return CategorizacionResult(
            calidad_didactica={
                "valoracion": cal_val,           # "positivo", "negativo", "neutral"
                "confianza": round(cal_conf, 3), # 0.0 a 1.0, redondeado a 3 decimales
                "palabras_clave": cal_palabras   # Lista de keywords encontradas
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
            tiempo_ms=tiempo_ms  # Tiempo de procesamiento para métricas
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
