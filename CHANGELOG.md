# Changelog

Todos los cambios notables en SentimentInsightUAM_SA se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

---

## [1.0.0] - 2025-11-09

### ✨ Lanzamiento Inicial - Módulo de Análisis de Sentimientos

#### 🎯 Características Principales

**Análisis de Sentimiento con BERT**
- Modelo por defecto: `dccuchile/bert-base-spanish-wwm-cased`
- Configuración flexible via variables de entorno
- Soporte para CPU, CUDA (NVIDIA GPU), MPS (Apple Silicon)
- Procesamiento en batch para eficiencia
- Cache automático de modelos descargados

**CLI Completo con 4 Comandos**
- `analizar`: Procesa opiniones pendientes de análisis
- `profesor --id N`: Analiza opiniones de un profesor específico
- `curso --name "Nombre"`: Analiza opiniones de un curso
- `stats`: Muestra estadísticas de análisis pendiente

**Conexión a Bases de Datos**
- PostgreSQL (async): Lectura de profesores, cursos, metadata
- MongoDB (async): Lectura/escritura de opiniones y análisis
- Comparte instancias Docker con proyecto principal
- Modelos ORM con SQLAlchemy 2.0 async
- Cliente MongoDB con Motor (async driver)

**Procesamiento de Opiniones**
- Clase `OpinionProcessor` para flujo completo
- Clase `SentimentAnalyzer` para análisis BERT
- Actualización automática de campo `sentimiento_general` en MongoDB
- Manejo robusto de errores y logging

#### 📦 Estructura del Proyecto

```
SentimentInsightUAM_SA/
├── src/
│   ├── cli.py                 # CLI principal
│   ├── core/                  # Utilidades (futuro)
│   ├── db/
│   │   ├── __init__.py        # Conexiones BD
│   │   ├── models.py          # Modelos ORM
│   │   └── repository.py      # Consultas
│   └── ml/
│       ├── __init__.py        # SentimentAnalyzer
│       └── processor.py       # OpinionProcessor
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── .github/copilot-instructions.md
```

#### 🔧 Dependencias Principales

- **ML/NLP**: `transformers>=4.35.0`, `torch>=2.0.0`, `scikit-learn>=1.3.0`
- **Bases de datos**: `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.29`, `motor>=3.3`
- **Utilidades**: `pydantic>=2.9`, `tenacity>=9.0`, `python-dotenv>=1.0`

#### 📊 Métricas

- **Archivos creados**: 12
- **Líneas de código**: ~1,500
- **Comandos CLI**: 4
- **Modelos BERT soportados**: 3+ (configurables)

#### 🎨 Características del Diseño

- **Arquitectura asíncrona**: Todo el stack usa async/await
- **Procesamiento en batch**: Análisis eficiente de múltiples textos
- **Singleton pattern**: Analizador BERT cargado una sola vez
- **Type hints completos**: Mejor autocompletado y detección de errores
- **Logging estructurado**: Mensajes informativos en todo el flujo

#### 🔒 Variables de Entorno

```env
# Bases de datos (compartidas con proyecto principal)
DATABASE_URL=postgresql+asyncpg://...
MONGO_URL=mongodb://...

# Modelo BERT
BERT_MODEL_NAME=dccuchile/bert-base-spanish-wwm-cased
DEVICE=cpu
BATCH_SIZE=8
MODEL_CACHE_DIR=./models/cache

# Configuración
LOG_LEVEL=INFO
DEBUG=false
```

#### 🚀 Próximos Pasos (Roadmap)

**Fase 2: Categorización por Aspectos (v1.1.0) - ✅ COMPLETADO**
- [x] Módulo de categorización (calidad didáctica, método evaluación, empatía)
- [x] Campo `categorizacion` en MongoDB
- [x] Integración en comandos existentes
- [ ] Modelo fine-tuned específico (Pendiente)

**Fase 3: API REST (v2.0.0)**
- [ ] FastAPI con endpoints de análisis
- [ ] Consulta de resultados por profesor/curso
- [ ] Estadísticas agregadas
- [ ] Documentación OpenAPI automática

**Fase 4: Visualización (v2.1.0)**
- [ ] Dashboard de resultados
- [ ] Gráficas de distribución de sentimientos
- [ ] Tendencias temporales
- [ ] Word clouds de opiniones

**Fase 5: Optimización (v3.0.0)**
- [ ] Fine-tuning de modelo BERT para dominio UAM
- [ ] Cache inteligente de resultados
- [ ] Procesamiento paralelo
- [ ] Soporte para GPU multi-card

---

## [1.1.0] - 2025-11-23

### 🚀 Mejoras en Análisis de Sentimiento

#### Cambio de Modelo Base
- **Nuevo Modelo**: `finiteautomata/beto-sentiment-analysis`
- **Motivo**: El modelo anterior (`dccuchile/bert-base-spanish-wwm-cased`) mostraba baja precisión en opiniones informales, clasificando erróneamente reseñas positivas como negativas.
- **Mejora**: Precisión drásticamente superior en detección de polaridad (Positivo/Negativo) en lenguaje natural de estudiantes.
- **Validación**: Pruebas con profesor "Josue Padilla" mostraron una correlación del ~95% con los datos de recomendación originales, frente al ~10% del modelo anterior.

#### ✨ Nueva Característica: Categorización por Aspectos
- Implementación de `OpinionCategorizer` para clasificar opiniones en 3 ejes:
    - **Calidad Didáctica**: Claridad, dominio del tema.
    - **Método de Evaluación**: Dificultad, tareas, exámenes.
    - **Empatía**: Trato al alumno, accesibilidad.
- Integración en el flujo de procesamiento (`OpinionProcessor`).
- Almacenamiento de resultados estructurados en MongoDB.

#### 🔧 Ajustes Técnicos
- Actualización de mapeo de etiquetas (labels) para soportar `POS`, `NEG`, `NEU` además de `POSITIVE`, `NEGATIVE`, `NEUTRAL`.
- Limpieza de cache de modelos para forzar la descarga del nuevo modelo optimizado.
- Actualización de documentación y ejemplos.

---

## [Unreleased]

### Planificado
- Worker asíncrono para procesamiento continuo
- Sistema de jobs programados con APScheduler
- Detección automática de idioma (español/inglés)
- Análisis de aspectos específicos (explicación, disponibilidad, etc.)
- Embeddings vectoriales para búsqueda semántica

---

**Última actualización**: 2025-11-09  
**Versión actual**: 1.0.0  
**Mantenedores**: Equipo SentimentInsightUAM - UAM Azcapotzalco
