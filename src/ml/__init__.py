"""
Módulo de análisis de sentimiento con BERT para SentimentInsightUAM_SA.

Implementa análisis de sentimiento general (Módulo 1) usando modelo RoBERTa/BERT
pre-entrenado en español.

Modelo por defecto: pysentimiento/robertuito-sentiment-analysis
- Etiquetas: POS (positivo), NEU (neutral), NEG (negativo)
- Entrenado con corpus TASS 2020 (~5k tweets en español)
- Base: RoBERTuito (RoBERTa entrenado en tweets en español)

Alternativas configurables vía variable de entorno BERT_MODEL_NAME.

Autor: SentimentInsightUAM Team
Fecha: 2025-11-09
"""

import os
import time
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline
)
import logging

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """
    Resultado del análisis de sentimiento.
    
    Attributes:
        clasificacion: positivo, neutral, negativo
        pesos: Dict con scores de cada clase
        confianza: Máximo score (0 a 1)
        tiempo_ms: Tiempo de procesamiento en milisegundos
    """
    clasificacion: str
    pesos: Dict[str, float]
    confianza: float
    tiempo_ms: int


class SentimentAnalyzer:
    """
    Analizador de sentimiento con modelo BERT.
    
    Carga el modelo una sola vez y reutiliza para múltiples predicciones.
    Soporta procesamiento en batch para eficiencia.
    """
    
    def __init__(
        self,
        model_name: str = None,
        device: str = None,
        cache_dir: str = None
    ):
        """
        Inicializa el analizador de sentimiento.
        
        Args:
            model_name: Nombre del modelo en HuggingFace Hub
            device: Dispositivo de cómputo (cpu, cuda, mps)
            cache_dir: Directorio para cache del modelo
        """
        self.model_name = model_name or os.getenv(
            "BERT_MODEL_NAME",
            "pysentimiento/robertuito-sentiment-analysis"
        )
        
        self.device = device or os.getenv("DEVICE", "cpu")
        self.cache_dir = cache_dir or os.getenv("MODEL_CACHE_DIR", "./models/cache")
        
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.model_version = None
        
        logger.info(f"Inicializando SentimentAnalyzer con modelo: {self.model_name}")
        logger.info(f"Dispositivo: {self.device}")
    
    def load_model(self) -> None:
        """
        Carga el modelo BERT y tokenizer.
        Descarga del Hub si no está en caché.
        """
        try:
            logger.info("Cargando modelo BERT...")
            
            # Crear directorio de cache si no existe
            os.makedirs(self.cache_dir, exist_ok=True)
            
            # Cargar tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            # Cargar modelo (usa la configuración de etiquetas del modelo)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            # Mover modelo a dispositivo
            if self.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.to("cuda")
                logger.info("Modelo cargado en GPU (CUDA)")
            elif self.device == "mps" and torch.backends.mps.is_available():
                self.model = self.model.to("mps")
                logger.info("Modelo cargado en GPU (Apple Silicon MPS)")
            else:
                self.model = self.model.to("cpu")
                logger.info("Modelo cargado en CPU")
            
            # Crear pipeline para simplificar predicciones
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" and torch.cuda.is_available() else -1
            )
            
            self.model_version = f"{self.model_name}-v1.0"
            
            logger.info(f"✓ Modelo {self.model_name} cargado exitosamente")
        
        except Exception as e:
            logger.error(f"✗ Error al cargar modelo {self.model_name}: {e}")
            raise
    
    def analizar(self, texto: str) -> SentimentResult:
        """
        Analiza el sentimiento de un texto individual.
        
        Args:
            texto: Texto a analizar
        
        Returns:
            SentimentResult con clasificación y pesos
        """
        # Cargar modelo si aún no está cargado (lazy loading)
        if self.pipeline is None:
            self.load_model()
        
        # Registrar tiempo de inicio para medir rendimiento
        inicio = time.time()
        
        try:
            # ================================================================
            # PASO 1: Ejecutar predicción del modelo
            # ================================================================
            # El pipeline procesa el texto y devuelve lista de resultados
            # texto[:512] -> Truncar a 512 caracteres (límite aproximado de tokens BERT)
            # [0] -> Tomar primer resultado (pipeline devuelve lista)
            # 
            # Formato de salida del modelo robertuito:
            # {'label': 'POS', 'score': 0.95}  <- clase ganadora y su probabilidad
            resultado = self.pipeline(texto[:512])[0]
            
            # ================================================================
            # PASO 2: Mapear etiqueta del modelo a español
            # ================================================================
            # El modelo robertuito devuelve: POS, NEU, NEG
            # Otros modelos pueden devolver: POSITIVE, NEGATIVE, NEUTRAL, LABEL_0, etc.
            # Este mapeo unifica todas las variantes a: positivo, neutral, negativo
            label_map = {
                "POSITIVE": "positivo",   # Formato de algunos modelos en inglés
                "NEGATIVE": "negativo",
                "NEUTRAL": "neutral",
                "POS": "positivo",         # Formato de robertuito/beto-sentiment
                "NEG": "negativo",
                "NEU": "neutral",
                "LABEL_0": "negativo",     # Formato genérico (índice -> clase)
                "LABEL_1": "neutral",
                "LABEL_2": "positivo"
            }
            
            # Obtener clasificación en español, por defecto "neutral" si no se encuentra
            clasificacion = label_map.get(resultado['label'], "neutral")
            
            # Score de confianza: probabilidad de la clase ganadora (0.0 a 1.0)
            confianza = float(resultado['score'])
            
            # ================================================================
            # PASO 3: Calcular pesos (distribución de probabilidades)
            # ================================================================
            # El pipeline solo devuelve la clase ganadora y su score.
            # Estimamos los pesos de las otras clases distribuyendo
            # la probabilidad restante (1 - confianza) equitativamente.
            #
            # Ejemplo: si clasificacion="positivo" y confianza=0.8
            #   - positivo: 0.8 (la confianza del modelo)
            #   - neutral:  0.1 (resto dividido entre 2)
            #   - negativo: 0.1 (resto dividido entre 2)
            pesos = {
                "positivo": confianza if clasificacion == "positivo" else (1 - confianza) / 2,
                "neutral": confianza if clasificacion == "neutral" else (1 - confianza) / 2,
                "negativo": confianza if clasificacion == "negativo" else (1 - confianza) / 2
            }
            
            # Normalizar pesos para garantizar que sumen exactamente 1.0
            # Esto corrige posibles errores de redondeo flotante
            total = sum(pesos.values())
            pesos = {k: v / total for k, v in pesos.items()}
            
            # ================================================================
            # PASO 4: Calcular tiempo de procesamiento
            # ================================================================
            # Tiempo en milisegundos desde el inicio del análisis
            tiempo_ms = int((time.time() - inicio) * 1000)
            
            # ================================================================
            # PASO 5: Construir y retornar resultado
            # ================================================================
            return SentimentResult(
                clasificacion=clasificacion,  # "positivo", "neutral" o "negativo"
                pesos=pesos,                  # Dict con probabilidades normalizadas
                confianza=confianza,          # Score de la clase ganadora
                tiempo_ms=tiempo_ms           # Tiempo de procesamiento
            )
        
        except Exception as e:
            logger.error(f"Error al analizar texto: {e}")
            raise
    
    def analizar_batch(
        self,
        textos: List[str],
        batch_size: int = None
    ) -> List[SentimentResult]:
        """
        Analiza múltiples textos en batch para mayor eficiencia.
        
        Args:
            textos: Lista de textos a analizar
            batch_size: Tamaño de batch (por defecto de .env)
        
        Returns:
            Lista de SentimentResult
        """
        if self.pipeline is None:
            self.load_model()
        
        batch_size = batch_size or int(os.getenv("BATCH_SIZE", "8"))
        
        inicio = time.time()
        
        try:
            # Truncar textos a 512 tokens
            textos_truncados = [t[:512] for t in textos]
            
            # Procesar en batch
            resultados_raw = self.pipeline(
                textos_truncados,
                batch_size=batch_size
            )
            
            tiempo_total_ms = int((time.time() - inicio) * 1000)
            tiempo_por_texto_ms = tiempo_total_ms // len(textos) if textos else 0
            
            # Convertir a SentimentResult
            resultados = []
            label_map = {
                "POSITIVE": "positivo",
                "NEGATIVE": "negativo",
                "NEUTRAL": "neutral",
                "POS": "positivo",
                "NEG": "negativo",
                "NEU": "neutral",
                "LABEL_0": "negativo",
                "LABEL_1": "neutral",
                "LABEL_2": "positivo"
            }
            
            for resultado in resultados_raw:
                clasificacion = label_map.get(resultado['label'], "neutral")
                confianza = float(resultado['score'])
                
                pesos = {
                    "positivo": confianza if clasificacion == "positivo" else (1 - confianza) / 2,
                    "neutral": confianza if clasificacion == "neutral" else (1 - confianza) / 2,
                    "negativo": confianza if clasificacion == "negativo" else (1 - confianza) / 2
                }
                
                total = sum(pesos.values())
                pesos = {k: v / total for k, v in pesos.items()}
                
                resultados.append(SentimentResult(
                    clasificacion=clasificacion,
                    pesos=pesos,
                    confianza=confianza,
                    tiempo_ms=tiempo_por_texto_ms
                ))
            
            logger.info(f"Procesados {len(textos)} textos en {tiempo_total_ms}ms")
            
            return resultados
        
        except Exception as e:
            logger.error(f"Error al analizar batch: {e}")
            raise
    
    def get_model_version(self) -> str:
        """
        Retorna la versión del modelo cargado.
        
        Returns:
            String con nombre y versión del modelo
        """
        return self.model_version or f"{self.model_name}-v1.0"


# ============================================================================
# FUNCIÓN AUXILIAR DE ALTO NIVEL
# ============================================================================

# Instancia global del analizador (singleton)
_global_analyzer: SentimentAnalyzer = None


def get_analyzer() -> SentimentAnalyzer:
    """
    Obtiene la instancia global del analizador (patrón singleton).
    
    Returns:
        SentimentAnalyzer configurado
    """
    global _global_analyzer
    
    if _global_analyzer is None:
        _global_analyzer = SentimentAnalyzer()
    
    return _global_analyzer


def analizar_sentimiento(texto: str) -> Dict[str, Any]:
    """
    Función de conveniencia para análisis rápido de un texto.
    
    Args:
        texto: Texto a analizar
    
    Returns:
        Dict con clasificación, pesos, confianza, modelo_version, tiempo_ms
    """
    analyzer = get_analyzer()
    resultado = analyzer.analizar(texto)
    
    return {
        "clasificacion": resultado.clasificacion,
        "pesos": resultado.pesos,
        "confianza": resultado.confianza,
        "modelo_version": analyzer.get_model_version(),
        "tiempo_procesamiento_ms": resultado.tiempo_ms
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "SentimentAnalyzer",
    "SentimentResult",
    "get_analyzer",
    "analizar_sentimiento",
]
