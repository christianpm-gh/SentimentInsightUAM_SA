# SentimentInsightUAM_SA

> **Módulo de Análisis de Sentimientos** para reseñas de profesores UAM Azcapotzalco

Sistema especializado de análisis de sentimientos usando modelos BERT pre-entrenados en español. Procesa opiniones almacenadas en MongoDB y actualiza resultados de clasificación (positivo/neutral/negativo).

---

## 📋 Descripción

**SentimentInsightUAM_SA** es el módulo de análisis de sentimientos del proyecto SentimentInsightUAM. Su función es:

1. **Leer opiniones** desde MongoDB (generadas por el módulo de scraping)
2. **Analizar sentimientos** usando modelos BERT
3. **Actualizar resultados** en la base de datos para consumo

### Relación con Proyecto Principal

```
┌────────────────────────────────┐
│    SentimentInsightUAM         │  Proyecto padre
│    (Scraping + Persistencia)   │  
│                                 │
│  ┌──────────┐   ┌──────────┐  │
│  │PostgreSQL│   │ MongoDB  │  │  Bases de datos
│  └────┬─────┘   └─────┬────┘  │  compartidas
│       │               │        │
└───────┼───────────────┼────────┘
        │               │
        ▼               ▼
┌────────────────────────────────┐
│  SentimentInsightUAM_SA        │  Este módulo
│  (Análisis de Sentimientos)    │  
│                                 │
│  ┌──────────────────────────┐ │
│  │   Modelo BERT            │ │
│  │   (Español)              │ │
│  └──────────────────────────┘ │
└────────────────────────────────┘
```

---

## ✨ Características

- ✅ **Análisis de sentimiento** con BERT pre-entrenado en español
- ✅ **Procesamiento en batch** para eficiencia
- ✅ **CLI intuitivo** con 4 comandos
- ✅ **Soporte multi-dispositivo** (CPU, CUDA, MPS)
- ✅ **Conexión asíncrona** a PostgreSQL + MongoDB
- ✅ **Configuración flexible** via variables de entorno

---

## 🚀 Instalación

### Prerrequisitos

**IMPORTANTE**: Este proyecto requiere que el proyecto principal esté corriendo:

1. **Bases de datos Docker** (desde `SentimentInsightUAM`):
   ```bash
   cd ~/dev/python-dev/SentimentInsightUAM
   make docker-up
   ```

2. **Python 3.11+** instalado

### Instalación del Módulo

```bash
# 1. Clonar/navegar al directorio
cd ~/dev/python-dev/SentimentInsightUAM_SA

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar entorno virtual
source venv/bin/activate

# 4. Actualizar pip
pip install --upgrade pip

# 5. Instalar dependencias
pip install -r requirements.txt

# 6. Copiar variables de entorno
cp .env.example .env
# Editar .env si es necesario
```

### Verificación de Instalación

```bash
# Activar venv
source venv/bin/activate

# Verificar Python
python --version
# Salida esperada: Python 3.11.x o 3.12.x

# Verificar PyTorch
python -c "import torch; print(f'PyTorch {torch.__version__}')"
# Salida esperada: PyTorch 2.x.x

# Verificar Transformers
python -c "import transformers; print(f'Transformers {transformers.__version__}')"
# Salida esperada: Transformers 4.35.x

# Verificar conexión a bases de datos
python -m src.cli stats
# Salida esperada: Estadísticas de opiniones pendientes
```

---

## 🎯 Uso

### Comandos Disponibles

#### 1. Analizar Opiniones Pendientes

Procesa opiniones que no tienen análisis de sentimiento:

```bash
# Analizar todas las opiniones pendientes
python -m src.cli analizar

# Analizar hasta 50 opiniones
python -m src.cli analizar --limit 50

# Analizar con batch size personalizado
python -m src.cli analizar --batch-size 16
```

**Salida esperada:**
```
================================================================================
ANÁLISIS DE SENTIMIENTO - Opiniones Pendientes
================================================================================

Total de opiniones pendientes: 250
Modelo BERT: dccuchile/bert-base-spanish-wwm-cased-v1.0

Procesando hasta 100 opiniones...

================================================================================
RESULTADO DEL ANÁLISIS
================================================================================
  Opiniones procesadas: 100
  Actualizaciones exitosas: 98
  Errores: 2

  Tasa de éxito: 98.0%
================================================================================
```

#### 2. Analizar Opiniones de un Profesor

Procesa opiniones de un profesor específico:

```bash
# Analizar profesor con ID 123
python -m src.cli profesor --id 123

# Analizar hasta 50 opiniones del profesor
python -m src.cli profesor --id 123 --limit 50
```

#### 3. Analizar Opiniones de un Curso

Procesa opiniones de un curso específico:

```bash
# Analizar curso "Estructura de Datos"
python -m src.cli curso --name "Estructura de Datos"

# Búsqueda parcial (regex case-insensitive)
python -m src.cli curso --name "Estructura"
```

#### 4. Ver Estadísticas

Muestra estadísticas de análisis:

```bash
python -m src.cli stats
```

**Salida esperada:**
```
================================================================================
ESTADÍSTICAS DE ANÁLISIS DE SENTIMIENTO
================================================================================

Opiniones pendientes de análisis: 250
Modelo BERT configurado: dccuchile/bert-base-spanish-wwm-cased-v1.0

================================================================================
```

---

## ⚙️ Configuración

### Variables de Entorno (`.env`)

```env
# ============================================================================
# Bases de Datos (Compartidas con proyecto principal)
# ============================================================================
DATABASE_URL=postgresql+asyncpg://sentiment_admin:dev_password_2024@localhost:5432/sentiment_uam_db
MONGO_URL=mongodb://sentiment_admin:dev_password_2024@localhost:27017/sentiment_uam_nlp?authSource=sentiment_uam_nlp

# ============================================================================
# Modelo BERT
# ============================================================================
# Modelo recomendado para español
BERT_MODEL_NAME=dccuchile/bert-base-spanish-wwm-cased

# Alternativas:
# BERT_MODEL_NAME=PlanTL-GOB-ES/roberta-base-bne
# BERT_MODEL_NAME=mrm8488/distilroberta-finetuned-sentiment-spa

# Ruta de cache del modelo (descarga automática)
MODEL_CACHE_DIR=./models/cache

# Dispositivo de cómputo
DEVICE=cpu  # Opciones: cpu, cuda (NVIDIA GPU), mps (Apple Silicon)

# Tamaño de batch para procesamiento
BATCH_SIZE=8

# ============================================================================
# Análisis
# ============================================================================
# Límite de opiniones por ejecución (-1 para sin límite)
MAX_OPINIONS_PER_RUN=-1

# Umbral de confianza (0.0 a 1.0)
CONFIDENCE_THRESHOLD=0.7

# ============================================================================
# Logging
# ============================================================================
LOG_LEVEL=INFO
DEBUG=false
```

### Modelos BERT Disponibles

| Modelo | Descripción | Tamaño |
|--------|-------------|--------|
| `dccuchile/bert-base-spanish-wwm-cased` | ✅ **Recomendado** - BERT base español | ~420MB |
| `PlanTL-GOB-ES/roberta-base-bne` | RoBERTa español (Gobierno España) | ~500MB |
| `mrm8488/distilroberta-finetuned-sentiment-spa` | DistilRoBERTa optimizado para sentimiento | ~300MB |

---

## 📊 Estructura del Proyecto

```
SentimentInsightUAM_SA/
├── src/
│   ├── __init__.py
│   ├── cli.py                 # CLI principal con 4 comandos
│   ├── core/                  # Utilidades core (futuro)
│   ├── db/
│   │   ├── __init__.py        # Conexiones async a BD
│   │   ├── models.py          # Modelos ORM (solo lectura)
│   │   └── repository.py      # Consultas especializadas
│   └── ml/
│       ├── __init__.py        # SentimentAnalyzer con BERT
│       └── processor.py       # OpinionProcessor (flujo completo)
├── data/
│   └── outputs/               # Resultados de análisis (futuro)
├── models/
│   └── cache/                 # Cache de modelos BERT
├── docs/                      # Documentación adicional
├── tests/                     # Tests (futuro)
├── .github/
│   └── copilot-instructions.md  # Contexto para Copilot
├── requirements.txt           # Dependencias Python
├── .env.example               # Template de variables de entorno
├── .gitignore                 # Archivos ignorados por Git
└── README.md                  # Este archivo
```

---

## 🔧 Desarrollo

### Activar Entorno Virtual

**SIEMPRE** activar antes de ejecutar código Python:

```bash
source venv/bin/activate
```

Verificar que estás en el venv correcto:

```bash
which python
# Debe mostrar: .../SentimentInsightUAM_SA/venv/bin/python
```

### Ejecutar CLI

```bash
# Formato correcto
python -m src.cli [comando] [opciones]

# Ejemplos
python -m src.cli analizar
python -m src.cli profesor --id 123
python -m src.cli stats
```

### Verificar Bases de Datos

Las bases de datos deben estar corriendo desde el proyecto principal:

```bash
# En otro terminal
cd ~/dev/python-dev/SentimentInsightUAM
make docker-up       # Iniciar contenedores
make db-status       # Verificar estado

# Conectar a MongoDB
make db-mongo
# Dentro: db.opiniones.countDocuments({})

# Conectar a PostgreSQL
make db-psql
# Dentro: SELECT COUNT(*) FROM profesores;
```

---

## 🤔 FAQ

### ¿Necesito descargar el modelo BERT manualmente?

**No.** La primera vez que ejecutes un comando de análisis, el modelo se descargará automáticamente desde HuggingFace Hub y se guardará en `./models/cache/`. Esto puede tardar 2-5 minutos dependiendo de tu conexión.

### ¿Puedo usar GPU para acelerar el análisis?

**Sí.** Cambia la variable `DEVICE` en `.env`:

```env
# Para NVIDIA GPU
DEVICE=cuda

# Para Apple Silicon (M1/M2/M3)
DEVICE=mps
```

Asegúrate de tener PyTorch instalado con soporte para tu GPU.

### ¿Qué pasa si las bases de datos no están corriendo?

El CLI mostrará un error de conexión. Inicia los contenedores Docker desde el proyecto principal:

```bash
cd ~/dev/python-dev/SentimentInsightUAM
make docker-up
```

### ¿Cómo actualizo el modelo BERT?

1. Cambia `BERT_MODEL_NAME` en `.env`
2. Elimina el cache: `rm -rf ./models/cache/`
3. Ejecuta cualquier comando de análisis (descargará el nuevo modelo)

---

## 📝 Licencia

Proyecto educativo - Universidad Autónoma Metropolitana (UAM) Azcapotzalco

---

## 👥 Equipo

**SentimentInsightUAM Team** - UAM Azcapotzalco

---

## 📚 Recursos

- [Documentación HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [Modelos BERT en español](https://huggingface.co/models?language=es&pipeline_tag=text-classification)
- [Proyecto principal SentimentInsightUAM](https://github.com/christianpm-gh/SentimentInsightUAM)

---

**Última actualización**: 2025-11-09  
**Versión**: 1.0.0
