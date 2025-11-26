# Arquitectura - SentimentInsightUAM_SA

Documentación detallada de la arquitectura del módulo de análisis de sentimientos.

---

## 📋 Índice

- [Visión General](#visión-general)
- [Componentes del Sistema](#componentes-del-sistema)
- [Flujo de Datos](#flujo-de-datos)
- [Modelo de Datos](#modelo-de-datos)
- [Patrones de Diseño](#patrones-de-diseño)
- [Tecnologías](#tecnologías)

---

## Visión General

SentimentInsightUAM_SA es un módulo especializado de NLP que procesa opiniones de profesores almacenadas en MongoDB y las enriquece con análisis de sentimiento y categorización por aspectos.

### Diagrama de Alto Nivel

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPAS DEL SISTEMA                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    CLI Layer                         │   │
│  │                   (src/cli.py)                       │   │
│  │  • Parseo de argumentos                              │   │
│  │  • Comandos: analizar, profesor, curso, stats        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Processing Layer                      │   │
│  │              (src/ml/processor.py)                   │   │
│  │  • OpinionProcessor: Orquestación del flujo          │   │
│  │  • Coordinación entre análisis y persistencia        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│              ┌────────────┴────────────┐                   │
│              ▼                         ▼                    │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │   ML Layer           │  │  Categorization      │        │
│  │  (src/ml/__init__)   │  │  (src/ml/categorizer)│        │
│  │  • SentimentAnalyzer │  │  • OpinionCategorizer│        │
│  │  • BERT Model        │  │  • Keyword Detection │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Data Layer                          │   │
│  │                   (src/db/)                          │   │
│  │  • Conexiones async (PostgreSQL + MongoDB)           │   │
│  │  • Modelos ORM (models.py)                           │   │
│  │  • Repositorio de consultas (repository.py)          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes del Sistema

### 1. CLI Layer (`src/cli.py`)

Punto de entrada del sistema. Gestiona la interfaz de línea de comandos.

```python
# Comandos disponibles
python -m src.cli analizar     # Procesa opiniones pendientes
python -m src.cli profesor     # Procesa por profesor
python -m src.cli curso        # Procesa por curso
python -m src.cli stats        # Muestra estadísticas
```

**Responsabilidades:**
- Parseo de argumentos con `argparse`
- Inicialización de bases de datos
- Delegación a `OpinionProcessor`
- Formato de salida en consola

### 2. Processing Layer (`src/ml/processor.py`)

Orquestador principal que coordina el flujo de procesamiento.

```python
class OpinionProcessor:
    """
    Coordina el flujo completo:
    1. Obtener opiniones de MongoDB
    2. Analizar con SentimentAnalyzer
    3. Categorizar con OpinionCategorizer
    4. Persistir resultados
    """
```

**Métodos principales:**
| Método | Descripción |
|--------|-------------|
| `procesar_pendientes()` | Procesa opiniones sin análisis |
| `procesar_por_profesor()` | Filtra por profesor |
| `procesar_por_curso()` | Filtra por curso |
| `obtener_estadisticas()` | Retorna contadores |

### 3. ML Layer (`src/ml/__init__.py`)

Implementa el análisis de sentimiento con BERT.

```python
class SentimentAnalyzer:
    """
    Analizador basado en modelo BERT pre-entrenado.
    Modelo: finiteautomata/beto-sentiment-analysis
    """
    
    def analizar(self, texto: str) -> SentimentResult:
        """Analiza un texto individual."""
        
    def analizar_batch(self, textos: List[str]) -> List[SentimentResult]:
        """Analiza múltiples textos en batch."""
```

**Dataclass de resultado:**
```python
@dataclass
class SentimentResult:
    clasificacion: str      # positivo, neutral, negativo
    pesos: Dict[str, float] # scores por clase
    confianza: float        # máximo score (0-1)
    tiempo_ms: int          # tiempo de procesamiento
```

### 4. Categorization Layer (`src/ml/categorizer.py`)

Clasificación de opiniones por aspectos usando detección de palabras clave.

```python
class OpinionCategorizer:
    """
    Categoriza en 3 dimensiones:
    - Calidad didáctica
    - Método de evaluación
    - Empatía
    """
    
    KEYWORDS = {
        "calidad_didactica": {
            "positivo": ["explica bien", "domina", "claro", ...],
            "negativo": ["no explica", "confuso", ...]
        },
        ...
    }
```

### 5. Data Layer (`src/db/`)

Gestiona conexiones y operaciones con bases de datos.

#### `src/db/__init__.py` - Conexiones

```python
# PostgreSQL (SQLAlchemy async)
async def get_db_session() -> AsyncSession
async def init_db() -> None
async def close_db() -> None

# MongoDB (Motor)
def get_mongo_client() -> AsyncIOMotorClient
def get_mongo_db() -> Database
async def init_mongo() -> None
async def close_mongo() -> None

# Inicialización completa
async def init_all_databases() -> None
async def close_all_databases() -> None
```

#### `src/db/models.py` - Modelos ORM

```python
class Profesor(Base):
    __tablename__ = "profesores"
    id: int
    nombre_completo: str
    slug: str
    departamento: str

class Curso(Base):
    __tablename__ = "cursos"
    id: int
    nombre: str
    departamento: str

class ReseniaMetadata(Base):
    __tablename__ = "resenias_metadata"
    id: int
    profesor_id: int
    curso_id: int
    mongo_opinion_id: str
```

#### `src/db/repository.py` - Consultas

```python
# PostgreSQL
async def obtener_profesor_por_id(session, id) -> Profesor
async def obtener_curso_por_id(session, id) -> Curso

# MongoDB
async def obtener_opiniones_pendientes_sentimiento(limit, skip) -> List[Dict]
async def actualizar_sentimiento_general(opinion_id, clasificacion, ...) -> bool
async def actualizar_categorizacion(opinion_id, ...) -> bool
```

---

## Flujo de Datos

### Flujo de Procesamiento Completo

```
┌─────────────────┐
│   Usuario CLI   │
└────────┬────────┘
         │ python -m src.cli analizar
         ▼
┌─────────────────┐
│    cli.main()   │
│                 │
│ • Parsea args   │
│ • Inicia DBs    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│      OpinionProcessor           │
│                                 │
│ 1. obtener_opiniones_pendientes │◀──── MongoDB
│ 2. Extraer textos               │
│ 3. analizar_batch (BERT)        │◀──── SentimentAnalyzer
│ 4. categorizar_batch            │◀──── OpinionCategorizer
│ 5. actualizar MongoDB           │────▶ MongoDB
└─────────────────────────────────┘
```

### Estructura de Opinión en MongoDB

```javascript
{
  "_id": ObjectId("..."),
  "profesor_id": 36,
  "curso": "Bases de Datos",
  "comentario": "Muy buen profesor...",
  "fecha": ISODate("2025-08-09"),
  
  // Resultado del análisis de sentimiento
  "sentimiento_general": {
    "analizado": true,
    "clasificacion": "positivo",
    "pesos": {
      "positivo": 0.998,
      "neutral": 0.001,
      "negativo": 0.001
    },
    "confianza": 0.998,
    "modelo_version": "finiteautomata/beto-sentiment-analysis-v1.0",
    "fecha_analisis": ISODate("2025-11-23"),
    "tiempo_procesamiento_ms": 45
  },
  
  // Resultado de la categorización
  "categorizacion": {
    "analizado": true,
    "calidad_didactica": {
      "valoracion": "positivo",
      "confianza": 1.0,
      "palabras_clave": ["domina", "buen profesor", "conocimiento"]
    },
    "metodo_evaluacion": {
      "valoracion": "neutral",
      "confianza": 0.5,
      "palabras_clave": []
    },
    "empatia": {
      "valoracion": "neutral",
      "confianza": 0.5,
      "palabras_clave": []
    },
    "modelo_version": "keyword-based-v1.0",
    "fecha_analisis": ISODate("2025-11-23"),
    "tiempo_procesamiento_ms": 2
  }
}
```

---

## Patrones de Diseño

### 1. Singleton Pattern

Usado para instancias únicas del analizador y categorizador.

```python
# src/ml/__init__.py
_global_analyzer: SentimentAnalyzer = None

def get_analyzer() -> SentimentAnalyzer:
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = SentimentAnalyzer()
    return _global_analyzer
```

**Beneficio**: El modelo BERT se carga una sola vez, evitando múltiples cargas costosas.

### 2. Repository Pattern

Abstrae el acceso a datos en `src/db/repository.py`.

```python
# Consultas encapsuladas
await obtener_opiniones_pendientes_sentimiento(limit=100)
await actualizar_sentimiento_general(opinion_id, ...)
```

**Beneficio**: Centraliza la lógica de acceso a datos, facilita testing y mantenimiento.

### 3. Async/Await Pattern

Todo el stack es asíncrono para máxima eficiencia.

```python
async def procesar_pendientes(self, limit: int = 100):
    opiniones = await obtener_opiniones_pendientes_sentimiento(limit)
    # Procesamiento...
    await actualizar_sentimiento_general(...)
```

**Beneficio**: Permite operaciones I/O no bloqueantes con bases de datos.

### 4. Batch Processing

Procesamiento en lotes para eficiencia.

```python
resultados = self.analyzer.analizar_batch(textos, batch_size=8)
```

**Beneficio**: Aprovecha la paralelización de GPUs y reduce overhead.

---

## Tecnologías

### Stack Principal

| Categoría | Tecnología | Versión | Uso |
|-----------|------------|---------|-----|
| **Lenguaje** | Python | 3.11+ | Base |
| **ML/NLP** | Transformers | 4.35+ | Modelos BERT |
| **ML/NLP** | PyTorch | 2.0+ | Backend ML |
| **DB Relacional** | SQLAlchemy | 2.0+ | ORM async |
| **DB Relacional** | asyncpg | 0.29+ | Driver PostgreSQL |
| **DB Documental** | Motor | 3.3+ | Cliente MongoDB async |
| **Validación** | Pydantic | 2.9+ | Validación de datos |

### Modelo de ML

```
Modelo: finiteautomata/beto-sentiment-analysis
├── Basado en: BETO (BERT español)
├── Entrenado en: Tweets en español
├── Clases: POS, NEU, NEG
├── Tamaño: ~440MB
└── Rendimiento: ~50ms/texto (CPU)
```

---

## Estructura de Directorios

```
SentimentInsightUAM_SA/
├── src/
│   ├── __init__.py           # Versión y metadata
│   ├── cli.py                # Punto de entrada CLI
│   ├── core/                 # Utilidades core
│   │   └── __init__.py
│   ├── db/                   # Capa de datos
│   │   ├── __init__.py       # Conexiones
│   │   ├── models.py         # Modelos ORM
│   │   └── repository.py     # Consultas
│   └── ml/                   # Capa de ML
│       ├── __init__.py       # SentimentAnalyzer
│       ├── categorizer.py    # OpinionCategorizer
│       └── processor.py      # OpinionProcessor
├── scripts/                  # Scripts de consulta
├── docs/                     # Documentación
├── models/
│   └── cache/               # Cache de modelos (gitignore)
├── requirements.txt
├── .env.example
└── README.md
```

---

**Última actualización**: 2025-11-26  
**Versión**: 1.1.0
