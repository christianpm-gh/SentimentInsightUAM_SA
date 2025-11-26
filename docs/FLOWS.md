# Flujos Críticos - SentimentInsightUAM_SA

Documentación detallada de los flujos de procesamiento del sistema.

---

## 📋 Índice

- [Flujo Principal de Análisis](#flujo-principal-de-análisis)
- [Flujo de Análisis de Sentimiento](#flujo-de-análisis-de-sentimiento)
- [Flujo de Categorización](#flujo-de-categorización)
- [Flujo de Persistencia](#flujo-de-persistencia)
- [Flujo de Conexiones](#flujo-de-conexiones)

---

## Flujo Principal de Análisis

### Descripción

El flujo principal procesa opiniones pendientes de análisis, aplicando tanto análisis de sentimiento como categorización por aspectos.

### Diagrama de Secuencia

```
┌─────────┐     ┌─────────┐     ┌────────────┐     ┌──────────────┐     ┌─────────┐
│  CLI    │     │Processor│     │ Analyzer   │     │ Categorizer  │     │ MongoDB │
└────┬────┘     └────┬────┘     └─────┬──────┘     └──────┬───────┘     └────┬────┘
     │               │                │                   │                  │
     │ analizar()    │                │                   │                  │
     │──────────────>│                │                   │                  │
     │               │                │                   │                  │
     │               │ get_pendientes()                                      │
     │               │───────────────────────────────────────────────────────>│
     │               │                │                   │                  │
     │               │<───────────────────────────────────────────────────────│
     │               │     [opiniones]                    │                  │
     │               │                │                   │                  │
     │               │ analizar_batch()                   │                  │
     │               │───────────────>│                   │                  │
     │               │                │                   │                  │
     │               │<───────────────│                   │                  │
     │               │  [SentimentResult]                 │                  │
     │               │                │                   │                  │
     │               │ categorizar_batch()                │                  │
     │               │────────────────────────────────────>│                  │
     │               │                │                   │                  │
     │               │<────────────────────────────────────│                  │
     │               │  [CategorizacionResult]            │                  │
     │               │                │                   │                  │
     │               │ actualizar_sentimiento()                              │
     │               │───────────────────────────────────────────────────────>│
     │               │                │                   │                  │
     │               │ actualizar_categorizacion()                           │
     │               │───────────────────────────────────────────────────────>│
     │               │                │                   │                  │
     │<──────────────│                │                   │                  │
     │   resultado   │                │                   │                  │
     │               │                │                   │                  │
```

### Código del Flujo

```python
# src/ml/processor.py

async def procesar_pendientes(self, limit: int = 100) -> Dict[str, Any]:
    """
    Flujo principal de procesamiento.
    """
    # 1. Inicializar analizadores
    await self.init_analyzer()
    
    # 2. Obtener opiniones pendientes de MongoDB
    opiniones = await obtener_opiniones_pendientes_sentimiento(limit=limit)
    
    # 3. Extraer textos
    textos = [op.get("comentario", "") for op in opiniones]
    opinion_ids = [str(op["_id"]) for op in opiniones]
    
    # 4. Analizar sentimiento en batch
    resultados_sentimiento = self.analyzer.analizar_batch(textos)
    
    # 5. Categorizar en batch
    resultados_categorizacion = self.categorizer.categorizar_batch(textos)
    
    # 6. Persistir resultados
    for opinion_id, sent, cat in zip(opinion_ids, resultados_sentimiento, resultados_categorizacion):
        await actualizar_sentimiento_general(opinion_id, sent.clasificacion, ...)
        await actualizar_categorizacion(opinion_id, cat.calidad_didactica, ...)
    
    return {"procesadas": len(opiniones), "exitosas": exitosas, "errores": errores}
```

---

## Flujo de Análisis de Sentimiento

### Descripción

El análisis de sentimiento utiliza un modelo BERT pre-entrenado para clasificar el texto en positivo, neutral o negativo.

### Diagrama

```
┌────────────────────────────────────────────────────────────────────┐
│                    ANÁLISIS DE SENTIMIENTO                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────┐      ┌─────────────┐      ┌────────────────────────┐ │
│  │  Texto  │─────▶│ Tokenizer   │─────▶│ BERT Model             │ │
│  │         │      │             │      │ (beto-sentiment)       │ │
│  └─────────┘      └─────────────┘      └───────────┬────────────┘ │
│                                                     │              │
│                                                     ▼              │
│                                        ┌────────────────────────┐ │
│                                        │ Softmax                │ │
│                                        │ • POS: 0.85            │ │
│                                        │ • NEU: 0.10            │ │
│                                        │ • NEG: 0.05            │ │
│                                        └───────────┬────────────┘ │
│                                                     │              │
│                                                     ▼              │
│                                        ┌────────────────────────┐ │
│                                        │ SentimentResult        │ │
│                                        │ • clasificacion: pos   │ │
│                                        │ • confianza: 0.85      │ │
│                                        │ • pesos: {...}         │ │
│                                        └────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Proceso Detallado

1. **Tokenización**: El texto se convierte a tokens usando el tokenizer de BERT
2. **Truncamiento**: Máximo 512 tokens (límite de BERT)
3. **Inferencia**: El modelo predice probabilidades para cada clase
4. **Mapeo de Labels**: `POS` → `positivo`, `NEU` → `neutral`, `NEG` → `negativo`
5. **Resultado**: Clasificación, confianza y pesos normalizados

### Código

```python
# src/ml/__init__.py

def analizar(self, texto: str) -> SentimentResult:
    # 1. Ejecutar pipeline
    resultado = self.pipeline(texto[:512])[0]
    
    # 2. Mapear labels
    label_map = {
        "POS": "positivo",
        "NEG": "negativo",
        "NEU": "neutral",
    }
    clasificacion = label_map.get(resultado['label'], "neutral")
    
    # 3. Calcular pesos normalizados
    confianza = float(resultado['score'])
    pesos = {
        "positivo": confianza if clasificacion == "positivo" else (1 - confianza) / 2,
        "neutral": confianza if clasificacion == "neutral" else (1 - confianza) / 2,
        "negativo": confianza if clasificacion == "negativo" else (1 - confianza) / 2
    }
    
    return SentimentResult(clasificacion=clasificacion, pesos=pesos, confianza=confianza, ...)
```

---

## Flujo de Categorización

### Descripción

La categorización clasifica opiniones en tres dimensiones usando detección de palabras clave.

### Diagrama

```
┌────────────────────────────────────────────────────────────────────┐
│                    CATEGORIZACIÓN POR ASPECTOS                     │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  "Muy buen profesor, domina la materia pero los exámenes    │  │
│  │   son difíciles. Es muy accesible y ayuda con las dudas."   │  │
│  └────────────────────────────┬────────────────────────────────┘  │
│                               │                                    │
│          ┌────────────────────┼────────────────────┐              │
│          ▼                    ▼                    ▼              │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐       │
│  │   CALIDAD     │   │  EVALUACIÓN   │   │    EMPATÍA    │       │
│  │   DIDÁCTICA   │   │               │   │               │       │
│  ├───────────────┤   ├───────────────┤   ├───────────────┤       │
│  │ ✓ domina      │   │ ✓ difíciles   │   │ ✓ accesible   │       │
│  │ ✓ buen profe  │   │   (negativo)  │   │ ✓ ayuda       │       │
│  │   (positivo)  │   │               │   │   (positivo)  │       │
│  └───────┬───────┘   └───────┬───────┘   └───────┬───────┘       │
│          │                   │                   │                │
│          ▼                   ▼                   ▼                │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐       │
│  │ POSITIVO      │   │ NEGATIVO      │   │ POSITIVO      │       │
│  │ conf: 1.0     │   │ conf: 1.0     │   │ conf: 1.0     │       │
│  └───────────────┘   └───────────────┘   └───────────────┘       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Palabras Clave por Categoría

```python
KEYWORDS = {
    "calidad_didactica": {
        "positivo": ["explica bien", "domina", "claro", "buen profesor", ...],
        "negativo": ["no explica", "confuso", "desorganizado", ...]
    },
    "metodo_evaluacion": {
        "positivo": ["justo", "razonable", "equilibrado", ...],
        "negativo": ["difícil", "exigente", "injusto", ...]
    },
    "empatia": {
        "positivo": ["comprensivo", "accesible", "ayuda", "amable", ...],
        "negativo": ["grosero", "inaccesible", "no ayuda", ...]
    }
}
```

### Algoritmo de Puntuación

```python
def _calcular_score_categoria(self, texto: str, categoria: str):
    texto_lower = texto.lower()
    
    # Contar matches
    positivas = [p for p in KEYWORDS[categoria]["positivo"] if p in texto_lower]
    negativas = [n for n in KEYWORDS[categoria]["negativo"] if n in texto_lower]
    
    total = len(positivas) + len(negativas)
    
    if total == 0:
        return "neutral", 0.5, []
    
    score_positivo = len(positivas) / total
    
    if score_positivo > 0.6:
        return "positivo", score_positivo, positivas
    elif score_positivo < 0.4:
        return "negativo", 1 - score_positivo, negativas
    else:
        return "neutral", 0.5, positivas + negativas
```

---

## Flujo de Persistencia

### Descripción

Los resultados del análisis se persisten en MongoDB, actualizando los campos `sentimiento_general` y `categorizacion`.

### Diagrama

```
┌────────────────────────────────────────────────────────────────────┐
│                    PERSISTENCIA EN MONGODB                         │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  DOCUMENTO ANTES                                             │  │
│  │  {                                                           │  │
│  │    "_id": ObjectId("..."),                                   │  │
│  │    "profesor_id": 36,                                        │  │
│  │    "comentario": "Muy buen profesor...",                     │  │
│  │    "sentimiento_general": { "analizado": false },            │  │
│  │    "categorizacion": { "analizado": false }                  │  │
│  │  }                                                           │  │
│  └────────────────────────────┬────────────────────────────────┘  │
│                               │                                    │
│                   ┌───────────▼───────────┐                       │
│                   │   PROCESAMIENTO       │                       │
│                   │   • Sentimiento       │                       │
│                   │   • Categorización    │                       │
│                   └───────────┬───────────┘                       │
│                               │                                    │
│                               ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  DOCUMENTO DESPUÉS                                           │  │
│  │  {                                                           │  │
│  │    "_id": ObjectId("..."),                                   │  │
│  │    "profesor_id": 36,                                        │  │
│  │    "comentario": "Muy buen profesor...",                     │  │
│  │    "sentimiento_general": {                                  │  │
│  │      "analizado": true,                                      │  │
│  │      "clasificacion": "positivo",                            │  │
│  │      "confianza": 0.95,                                      │  │
│  │      "pesos": { "positivo": 0.95, "neutral": 0.03, ... },   │  │
│  │      "modelo_version": "beto-sentiment-v1.0",                │  │
│  │      "fecha_analisis": ISODate("2025-11-26"),                │  │
│  │      "tiempo_procesamiento_ms": 45                           │  │
│  │    },                                                        │  │
│  │    "categorizacion": {                                       │  │
│  │      "analizado": true,                                      │  │
│  │      "calidad_didactica": { ... },                           │  │
│  │      "metodo_evaluacion": { ... },                           │  │
│  │      "empatia": { ... },                                     │  │
│  │      "modelo_version": "keyword-based-v1.0",                 │  │
│  │      "fecha_analisis": ISODate("2025-11-26"),                │  │
│  │      "tiempo_procesamiento_ms": 2                            │  │
│  │    }                                                         │  │
│  │  }                                                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Operaciones de Actualización

```python
# src/db/repository.py

async def actualizar_sentimiento_general(opinion_id, clasificacion, pesos, confianza, ...):
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
                "tiempo_procesamiento_ms": tiempo_ms
            }
        }}
    )
    return result.modified_count > 0
```

---

## Flujo de Conexiones

### Descripción

El sistema mantiene conexiones asíncronas a PostgreSQL y MongoDB.

### Diagrama

```
┌────────────────────────────────────────────────────────────────────┐
│                    GESTIÓN DE CONEXIONES                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                     INICIALIZACIÓN                          │   │
│  │                  init_all_databases()                       │   │
│  └─────────────────────────┬──────────────────────────────────┘   │
│                            │                                       │
│           ┌────────────────┴────────────────┐                     │
│           ▼                                 ▼                      │
│  ┌─────────────────────┐         ┌─────────────────────┐          │
│  │    PostgreSQL       │         │      MongoDB        │          │
│  │    init_db()        │         │    init_mongo()     │          │
│  ├─────────────────────┤         ├─────────────────────┤          │
│  │ • SQLAlchemy Engine │         │ • Motor Client      │          │
│  │ • Pool de conexiones│         │ • Singleton pattern │          │
│  │ • async_sessionmaker│         │ • Ping de verificar │          │
│  └──────────┬──────────┘         └──────────┬──────────┘          │
│             │                               │                      │
│             ▼                               ▼                      │
│  ┌─────────────────────┐         ┌─────────────────────┐          │
│  │   get_db_session()  │         │   get_mongo_db()    │          │
│  │   (context manager) │         │   (database ref)    │          │
│  └─────────────────────┘         └─────────────────────┘          │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                      CIERRE                                 │   │
│  │                  close_all_databases()                      │   │
│  └─────────────────────────┬──────────────────────────────────┘   │
│                            │                                       │
│           ┌────────────────┴────────────────┐                     │
│           ▼                                 ▼                      │
│  ┌─────────────────────┐         ┌─────────────────────┐          │
│  │    close_db()       │         │   close_mongo()     │          │
│  │ engine.dispose()    │         │ client.close()      │          │
│  └─────────────────────┘         └─────────────────────┘          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Código de Inicialización

```python
# src/db/__init__.py

async def init_all_databases() -> None:
    """Inicializa todas las conexiones."""
    logger.info("Inicializando conexiones a bases de datos...")
    await init_db()      # PostgreSQL
    await init_mongo()   # MongoDB
    logger.info("✓ Todas las bases de datos conectadas")

async def close_all_databases() -> None:
    """Cierra todas las conexiones."""
    logger.info("Cerrando conexiones a bases de datos...")
    await close_db()
    await close_mongo()
    logger.info("✓ Todas las bases de datos desconectadas")
```

---

**Última actualización**: 2025-11-26  
**Versión**: 1.1.0
