# SentimentInsightUAM_SA

> **Módulo de Análisis de Sentimientos** para reseñas de profesores UAM Azcapotzalco

Sistema especializado de análisis de sentimientos usando modelos BERT pre-entrenados en español. Procesa opiniones almacenadas en MongoDB y actualiza resultados de clasificación (positivo/neutral/negativo) con categorización por aspectos (calidad didáctica, método de evaluación, empatía).

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Version 1.1.0](https://img.shields.io/badge/version-1.1.0-green.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📑 Índice

- [Descripción](#-descripción)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Instalación Rápida](#-instalación-rápida)
- [Uso](#-uso)
- [Configuración](#-configuración)
- [Scripts de Consulta](#-scripts-de-consulta)
- [Desarrollo](#-desarrollo)
- [FAQ](#-faq)
- [Documentación Adicional](#-documentación-adicional)

---

## 📋 Descripción

**SentimentInsightUAM_SA** es el módulo de análisis de sentimientos del proyecto SentimentInsightUAM. Su función es:

1. **Leer opiniones** desde MongoDB (generadas por el módulo de scraping)
2. **Analizar sentimientos** usando modelo BERT optimizado para español
3. **Categorizar opiniones** en tres dimensiones: calidad didáctica, método de evaluación, empatía
4. **Actualizar resultados** en la base de datos para consumo

### Relación con Proyecto Principal

```
┌─────────────────────────────────────┐
│       SentimentInsightUAM           │  Proyecto padre
│     (Scraping + Persistencia)       │  (recolección de datos)
│                                     │
│  ┌────────────┐   ┌────────────┐   │
│  │ PostgreSQL │   │  MongoDB   │   │  Bases de datos
│  │  (Metadatos)│   │ (Opiniones)│   │  compartidas via Docker
│  └──────┬─────┘   └─────┬──────┘   │
└─────────┼───────────────┼──────────┘
          │               │
          ▼               ▼
┌─────────────────────────────────────┐
│     SentimentInsightUAM_SA          │  Este módulo
│   (Análisis de Sentimientos)        │  (procesamiento NLP)
│                                     │
│  ┌─────────────────────────────┐   │
│  │  BERT (beto-sentiment)       │   │
│  │  + Categorización Aspectos   │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## ✨ Características

### Análisis de Sentimiento (v1.0.0)
- ✅ **Modelo BERT optimizado**: `finiteautomata/beto-sentiment-analysis`
- ✅ **Procesamiento en batch** para eficiencia
- ✅ **CLI intuitivo** con 4 comandos
- ✅ **Soporte multi-dispositivo** (CPU, CUDA, MPS)
- ✅ **Conexión asíncrona** a PostgreSQL + MongoDB
- ✅ **Configuración flexible** via variables de entorno

### Categorización por Aspectos (v1.1.0)
- ✅ **Calidad Didáctica**: Claridad, dominio del tema, metodología
- ✅ **Método de Evaluación**: Dificultad, justicia, carga de trabajo
- ✅ **Empatía**: Trato al alumno, accesibilidad, comprensión

---

## 🏗️ Arquitectura

> Documentación completa en [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

```
SentimentInsightUAM_SA/
├── src/
│   ├── cli.py                 # CLI principal (4 comandos)
│   ├── core/                  # Utilidades core
│   ├── db/
│   │   ├── __init__.py        # Conexiones async (PostgreSQL + MongoDB)
│   │   ├── models.py          # Modelos ORM SQLAlchemy
│   │   └── repository.py      # Consultas y actualizaciones
│   └── ml/
│       ├── __init__.py        # SentimentAnalyzer (BERT)
│       ├── categorizer.py     # OpinionCategorizer (aspectos)
│       └── processor.py       # OpinionProcessor (orquestación)
├── scripts/                   # Scripts de consulta y análisis
├── docs/                      # Documentación detallada
├── requirements.txt           # Dependencias Python
└── .env.example               # Template de configuración
```

### Flujo de Procesamiento

```
┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   MongoDB   │───▶│ OpinionProcessor │───▶│ SentimentAnalyzer│
│ (opiniones) │    │  (orquestador)   │    │     (BERT)       │
└─────────────┘    └────────┬────────┘    └──────────────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │OpinionCategorizer│
                   │   (aspectos)     │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────┐
                   │   MongoDB   │
                   │(resultados) │
                   └─────────────┘
```

---

## 🚀 Instalación Rápida

> Guía completa en [`docs/SETUP.md`](docs/SETUP.md)

### Prerrequisitos

**IMPORTANTE**: Este proyecto requiere que las bases de datos del proyecto principal estén corriendo:

```bash
# Desde el proyecto principal SentimentInsightUAM
cd ~/dev/python-dev/SentimentInsightUAM
docker-compose up -d
```

- **Python 3.11+**
- **Docker** (para bases de datos)
- **~2GB de espacio** (para modelos BERT)

### Instalación del Módulo

```bash
# 1. Clonar repositorio
git clone https://github.com/christianpm-gh/SentimentInsightUAM_SA.git
cd SentimentInsightUAM_SA

# 2. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env si es necesario
```

### Verificación de Instalación

```bash
# Verificar Python
python --version    # Python 3.11.x o 3.12.x

# Verificar dependencias clave
python -c "import torch; print(f'PyTorch {torch.__version__}')"
python -c "import transformers; print(f'Transformers {transformers.__version__}')"

# Verificar conexión a bases de datos
python -m src.cli stats
```

---

## 🎯 Uso

### Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `analizar` | Procesa opiniones pendientes de análisis |
| `profesor --id N` | Analiza opiniones de un profesor específico |
| `curso --name "..."` | Analiza opiniones de un curso |
| `stats` | Muestra estadísticas de análisis pendiente |

#### 1. Analizar Opiniones Pendientes

```bash
# Analizar todas las opiniones pendientes
python -m src.cli analizar

# Analizar hasta 50 opiniones
python -m src.cli analizar --limit 50

# Analizar con batch size personalizado
python -m src.cli analizar --batch-size 16

# Omitir las primeras 100 opiniones
python -m src.cli analizar --skip 100
```

#### 2. Analizar Opiniones de un Profesor

```bash
# Analizar profesor con ID 123
python -m src.cli profesor --id 123

# Analizar hasta 50 opiniones del profesor
python -m src.cli profesor --id 123 --limit 50
```

#### 3. Analizar Opiniones de un Curso

```bash
# Analizar curso específico
python -m src.cli curso --name "Estructura de Datos"

# Búsqueda parcial (regex case-insensitive)
python -m src.cli curso --name "Programación"
```

#### 4. Ver Estadísticas

```bash
python -m src.cli stats
```

### Ejemplo de Salida

```
================================================================================
ANÁLISIS DE SENTIMIENTO - Opiniones Pendientes
================================================================================

Total de opiniones pendientes: 250
Modelo utilizado: finiteautomata/beto-sentiment-analysis-v1.0

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

---

## ⚙️ Configuración

### Variables de Entorno (`.env`)

```env
# ============================================================================
# Bases de Datos (compartidas con proyecto principal)
# ============================================================================
DATABASE_URL=postgresql+asyncpg://sentiment_admin:dev_password_2024@localhost:5432/sentiment_uam_db
MONGO_URL=mongodb://sentiment_admin:dev_password_2024@localhost:27017/sentiment_uam_nlp?authSource=sentiment_uam_nlp

# ============================================================================
# Modelo BERT
# ============================================================================
BERT_MODEL_NAME=finiteautomata/beto-sentiment-analysis
MODEL_CACHE_DIR=./models/cache
DEVICE=cpu  # Opciones: cpu, cuda, mps

# ============================================================================
# Procesamiento
# ============================================================================
BATCH_SIZE=8
MAX_OPINIONS_PER_RUN=-1
CONFIDENCE_THRESHOLD=0.7

# ============================================================================
# Logging
# ============================================================================
LOG_LEVEL=INFO
DEBUG=false
```

### Modelos BERT Disponibles

| Modelo | Descripción | Uso Recomendado |
|--------|-------------|-----------------|
| `finiteautomata/beto-sentiment-analysis` | **Recomendado** - BETO afinado para sentimientos | Opiniones informales |
| `dccuchile/bert-base-spanish-wwm-cased` | BERT base español | Texto formal |
| `PlanTL-GOB-ES/roberta-base-bne` | RoBERTa español | Texto general |

---

## 📊 Scripts de Consulta

El directorio `scripts/` contiene utilidades para explorar y visualizar resultados:

| Script | Descripción |
|--------|-------------|
| `listar_profesores.py` | Lista profesores disponibles |
| `listar_materias.py` | Lista materias con conteo de opiniones |
| `analisis_profesor.py` | Estadísticas detalladas de un profesor |
| `analisis_materia.py` | Estadísticas detalladas de una materia |
| `ver_opinion.py` | Detalles de una opinión específica |

```bash
# Ejemplos de uso
python scripts/listar_profesores.py --limit 50
python scripts/analisis_profesor.py 36
python scripts/analisis_materia.py "Estructura de Datos"
```

> Documentación completa en [`scripts/README.md`](scripts/README.md)

---

## 🔧 Desarrollo

> Guía completa en [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)

### Entorno de Desarrollo

```bash
# SIEMPRE activar el entorno virtual
source venv/bin/activate

# Verificar que estás en el venv correcto
which python  # .../SentimentInsightUAM_SA/venv/bin/python
```

### Estructura del Código

| Módulo | Responsabilidad |
|--------|-----------------|
| `src/cli.py` | Punto de entrada CLI, parseo de argumentos |
| `src/db/` | Conexiones a bases de datos, modelos ORM |
| `src/ml/__init__.py` | `SentimentAnalyzer` - Análisis con BERT |
| `src/ml/categorizer.py` | `OpinionCategorizer` - Clasificación por aspectos |
| `src/ml/processor.py` | `OpinionProcessor` - Orquestación del flujo |

### Flujos Críticos

> Documentación completa en [`docs/FLOWS.md`](docs/FLOWS.md)

1. **Análisis de Sentimiento**: Opinión → BERT → Clasificación (pos/neu/neg)
2. **Categorización**: Opinión → Keywords → Aspectos (didáctica/evaluación/empatía)
3. **Persistencia**: Resultados → MongoDB (campo `sentimiento_general` y `categorizacion`)

---

## 🤔 FAQ

<details>
<summary><strong>¿Necesito descargar el modelo BERT manualmente?</strong></summary>

No. La primera vez que ejecutes un comando de análisis, el modelo se descargará automáticamente desde HuggingFace Hub y se guardará en `./models/cache/`. Esto puede tardar 2-5 minutos dependiendo de tu conexión.
</details>

<details>
<summary><strong>¿Puedo usar GPU para acelerar el análisis?</strong></summary>

Sí. Cambia la variable `DEVICE` en `.env`:

```env
DEVICE=cuda  # NVIDIA GPU
DEVICE=mps   # Apple Silicon (M1/M2/M3)
```

Asegúrate de tener PyTorch instalado con soporte para tu GPU.
</details>

<details>
<summary><strong>¿Qué pasa si las bases de datos no están corriendo?</strong></summary>

El CLI mostrará un error de conexión. Inicia los contenedores Docker desde el proyecto principal:

```bash
cd ~/dev/python-dev/SentimentInsightUAM
docker-compose up -d
```
</details>

<details>
<summary><strong>¿Cómo actualizo el modelo BERT?</strong></summary>

1. Cambia `BERT_MODEL_NAME` en `.env`
2. Elimina el cache: `rm -rf ./models/cache/`
3. Ejecuta cualquier comando de análisis (descargará el nuevo modelo)
</details>

<details>
<summary><strong>¿Cuál es la diferencia entre sentimiento y categorización?</strong></summary>

- **Sentimiento general**: Clasificación global (positivo/neutral/negativo) usando BERT
- **Categorización**: Análisis por aspectos específicos (calidad didáctica, método de evaluación, empatía) usando detección de palabras clave
</details>

---

## 📚 Documentación Adicional

| Documento | Descripción |
|-----------|-------------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Arquitectura detallada del sistema |
| [`docs/SETUP.md`](docs/SETUP.md) | Guía completa de instalación |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | Guía de desarrollo y contribución |
| [`docs/FLOWS.md`](docs/FLOWS.md) | Flujos críticos del sistema |
| [`scripts/README.md`](scripts/README.md) | Documentación de scripts de consulta |
| [`CHANGELOG.md`](CHANGELOG.md) | Historial de cambios |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Guía para contribuidores |

---

## 📝 Licencia

Proyecto educativo - Universidad Autónoma Metropolitana (UAM) Azcapotzalco

---

## 👥 Equipo

**SentimentInsightUAM Team** - UAM Azcapotzalco

---

## 🔗 Enlaces

- [Proyecto principal SentimentInsightUAM](https://github.com/christianpm-gh/SentimentInsightUAM)
- [Documentación HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [Modelo BETO Sentiment Analysis](https://huggingface.co/finiteautomata/beto-sentiment-analysis)

---

**Versión**: 1.1.0  
**Última actualización**: 2025-11-26
