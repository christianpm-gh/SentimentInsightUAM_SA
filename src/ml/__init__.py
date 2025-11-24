"""
Módulo de análisis de sentimiento con BERT para SentimentInsightUAM_SA.

Implementa análisis de sentimiento general (Módulo 1) usando modelo BERT
pre-entrenado en español.

Modelo por defecto: dccuchile/bert-base-spanish-wwm-cased
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
            "dccuchile/bert-base-spanish-wwm-cased"
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
            
            # Cargar modelo
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                num_labels=3  # positivo, neutral, negativo
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
            
            logger.info("✓ Modelo BERT cargado exitosamente")
        
        except Exception as e:
            logger.error(f"✗ Error al cargar modelo BERT: {e}")
            raise
    
    def analizar(self, texto: str) -> SentimentResult:
        """
        Analiza el sentimiento de un texto individual.
        
        Args:
            texto: Texto a analizar
        
        Returns:
            SentimentResult con clasificación y pesos
        """
        if self.pipeline is None:
            self.load_model()
        
        inicio = time.time()
        
        try:
            # Ejecutar predicción
            resultado = self.pipeline(texto[:512])[0]  # BERT max 512 tokens
            
            # Mapear label a clasificación
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
            
            clasificacion = label_map.get(resultado['label'], "neutral")
            confianza = float(resultado['score'])
            
            # Crear pesos (simulados si el modelo no los provee directamente)
            pesos = {
                "positivo": confianza if clasificacion == "positivo" else (1 - confianza) / 2,
                "neutral": confianza if clasificacion == "neutral" else (1 - confianza) / 2,
                "negativo": confianza if clasificacion == "negativo" else (1 - confianza) / 2
            }
            
            # Normalizar pesos para que sumen 1
            total = sum(pesos.values())
            pesos = {k: v / total for k, v in pesos.items()}
            
            tiempo_ms = int((time.time() - inicio) * 1000)
            
            return SentimentResult(
                clasificacion=clasificacion,
                pesos=pesos,
                confianza=confianza,
                tiempo_ms=tiempo_ms
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
