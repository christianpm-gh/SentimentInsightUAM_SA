# Guía de Instalación - SentimentInsightUAM_SA

Guía completa para instalar y configurar el módulo de análisis de sentimientos.

---

## 📋 Índice

- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación Paso a Paso](#instalación-paso-a-paso)
- [Configuración](#configuración)
- [Verificación](#verificación)
- [Solución de Problemas](#solución-de-problemas)

---

## Requisitos del Sistema

### Hardware Mínimo

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| RAM | 4 GB | 8 GB |
| Disco | 3 GB | 5 GB |
| CPU | 2 cores | 4 cores |
| GPU | No requerida | NVIDIA con CUDA |

### Software

| Software | Versión | Notas |
|----------|---------|-------|
| Python | 3.11+ | 3.12 recomendado |
| Docker | 20.10+ | Para bases de datos |
| Git | 2.30+ | Control de versiones |

### Bases de Datos (desde proyecto principal)

El proyecto principal `SentimentInsightUAM` debe estar corriendo con Docker:

```bash
cd ~/dev/python-dev/SentimentInsightUAM
docker-compose up -d
```

Esto levanta:
- **PostgreSQL**: `localhost:5432`
- **MongoDB**: `localhost:27017`

---

## Instalación Paso a Paso

### 1. Clonar el Repositorio

```bash
# Clonar
git clone https://github.com/christianpm-gh/SentimentInsightUAM_SA.git
cd SentimentInsightUAM_SA
```

### 2. Crear Entorno Virtual

```bash
# Crear venv
python3 -m venv venv

# Activar (Linux/macOS)
source venv/bin/activate

# Activar (Windows)
.\venv\Scripts\activate
```

> ⚠️ **IMPORTANTE**: Siempre activar el entorno virtual antes de trabajar.

### 3. Instalar Dependencias

```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

Esto instalará:
- PyTorch (~2GB)
- Transformers
- SQLAlchemy + asyncpg
- Motor (MongoDB)
- Y otras dependencias

### 4. Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar si es necesario
nano .env  # o tu editor preferido
```

### 5. Primera Ejecución (Descarga de Modelo)

La primera ejecución descargará el modelo BERT (~440MB):

```bash
python -m src.cli stats
```

---

## Configuración

### Variables de Entorno

Archivo `.env`:

```env
# ============================================================================
# Bases de Datos
# ============================================================================
DATABASE_URL=postgresql+asyncpg://sentiment_admin:dev_password_2024@localhost:5432/sentiment_uam_db
MONGO_URL=mongodb://sentiment_admin:dev_password_2024@localhost:27017/sentiment_uam_nlp?authSource=sentiment_uam_nlp

# ============================================================================
# Modelo BERT
# ============================================================================
BERT_MODEL_NAME=finiteautomata/beto-sentiment-analysis
MODEL_CACHE_DIR=./models/cache
DEVICE=cpu

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

### Opciones de Dispositivo

| Valor | Descripción | Requisitos |
|-------|-------------|------------|
| `cpu` | Procesador (default) | Ninguno extra |
| `cuda` | GPU NVIDIA | CUDA + cuDNN |
| `mps` | Apple Silicon | macOS M1/M2/M3 |

### Configuración para GPU NVIDIA

```bash
# Instalar PyTorch con CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu118

# Verificar
python -c "import torch; print(torch.cuda.is_available())"

# Actualizar .env
DEVICE=cuda
```

### Configuración para Apple Silicon

```bash
# Verificar MPS
python -c "import torch; print(torch.backends.mps.is_available())"

# Actualizar .env
DEVICE=mps
```

---

## Verificación

### 1. Verificar Python

```bash
python --version
# Python 3.11.x o superior
```

### 2. Verificar Dependencias

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
python -c "import motor; print(f'Motor: {motor.version}')"
```

### 3. Verificar Bases de Datos

```bash
# PostgreSQL
docker ps | grep postgres
# Debe mostrar contenedor corriendo

# MongoDB
docker ps | grep mongo
# Debe mostrar contenedor corriendo
```

### 4. Verificar CLI

```bash
python -m src.cli stats
```

Salida esperada:
```
================================================================================
ESTADÍSTICAS DE ANÁLISIS DE SENTIMIENTO
================================================================================

Opiniones pendientes de análisis: X
Modelo configurado: finiteautomata/beto-sentiment-analysis-v1.0

================================================================================
```

### 5. Verificar Análisis

```bash
# Analizar una opinión de prueba
python -m src.cli analizar --limit 1
```

---

## Solución de Problemas

### Error: Conexión a PostgreSQL

```
Error: Connection refused to localhost:5432
```

**Solución**: Verificar que Docker esté corriendo:
```bash
cd ~/dev/python-dev/SentimentInsightUAM
docker-compose up -d
docker-compose ps
```

### Error: Conexión a MongoDB

```
Error: ServerSelectionTimeoutError
```

**Solución**: Verificar MongoDB:
```bash
docker-compose logs mongo
```

### Error: Modelo no encontrado

```
OSError: Can't load model 'finiteautomata/beto-sentiment-analysis'
```

**Solución**: Verificar conexión a internet y eliminar cache:
```bash
rm -rf ./models/cache/
python -m src.cli stats
```

### Error: CUDA out of memory

```
RuntimeError: CUDA out of memory
```

**Solución**: Reducir batch size:
```env
BATCH_SIZE=4  # o incluso 2
```

O usar CPU:
```env
DEVICE=cpu
```

### Error: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'transformers'
```

**Solución**: Verificar entorno virtual:
```bash
which python
# Debe mostrar: .../SentimentInsightUAM_SA/venv/bin/python

# Si no, activar:
source venv/bin/activate

# Reinstalar dependencias:
pip install -r requirements.txt
```

---

## Estructura Post-Instalación

Después de la instalación, la estructura debe verse así:

```
SentimentInsightUAM_SA/
├── venv/                    # Entorno virtual (creado)
├── models/
│   └── cache/              # Cache de modelos (después de primera ejecución)
├── .env                    # Variables de entorno (creado)
├── src/
├── scripts/
├── docs/
├── requirements.txt
└── README.md
```

---

## Próximos Pasos

1. **Explorar el CLI**: [`python -m src.cli --help`](../README.md#uso)
2. **Leer la arquitectura**: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)
3. **Guía de desarrollo**: [`docs/DEVELOPMENT.md`](DEVELOPMENT.md)
4. **Scripts de consulta**: [`scripts/README.md`](../scripts/README.md)

---

**Última actualización**: 2025-11-26  
**Versión**: 1.1.0
