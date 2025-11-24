# Instrucciones para GitHub Copilot - SentimentInsightUAM_SA

Este archivo proporciona contexto permanente a GitHub Copilot para asistir efectivamente en el desarrollo del módulo de análisis de sentimientos.

---

## 📁 Contexto del Proyecto

### Propósito
Módulo especializado de análisis de sentimientos para opiniones de profesores UAM almacenadas en MongoDB. Este proyecto **NO incluye scraping**, solo lectura y análisis de datos existentes.

### Relación con Proyecto Principal
- **Proyecto padre**: `SentimentInsightUAM` (scraping y persistencia)
- **Este proyecto**: `SentimentInsightUAM_SA` (análisis de sentimientos)
- **Bases de datos compartidas**: PostgreSQL + MongoDB (mismas instancias via Docker)

### Tecnologías Core
- **Python 3.11+**
- **SQLAlchemy 2.0** (async) - Lectura de PostgreSQL
- **Motor** - Cliente MongoDB asíncrono
- **Transformers** (HuggingFace) - Modelos BERT
- **PyTorch** - Backend para BERT
- **pydantic** - Validación de datos

---

## 🏗️ Arquitectura

```
src/
├── cli.py                 # CLI con 4 comandos: analizar, profesor, curso, stats
├── core/                  # Utilidades core (futuro)
├── db/
│   ├── __init__.py        # Conexiones async a PostgreSQL + MongoDB
│   ├── models.py          # Modelos ORM (solo lectura)
│   └── repository.py      # Consultas especializadas
└── ml/
    ├── __init__.py        # SentimentAnalyzer con BERT
    └── processor.py       # OpinionProcessor (flujo completo)
```

---

## 🔑 Características Implementadas (v1.0.0)

### ✅ Conexión a Bases de Datos
- **PostgreSQL**: Lectura de profesores, cursos, reseñas metadata
- **MongoDB**: Lectura/escritura de opiniones con análisis
- **Asíncrono total**: SQLAlchemy async + Motor

### ✅ Análisis de Sentimiento con BERT
- **Modelo por defecto**: `finiteautomata/beto-sentiment-analysis`
- **Configuración**: Variables de entorno (.env)
- **Soporte batch**: Procesamiento eficiente de múltiples textos
- **Dispositivos**: CPU, CUDA (GPU NVIDIA), MPS (Apple Silicon)

### ✅ CLI Completo
1. **`analizar`** - Procesa opiniones pendientes
2. **`profesor --id N`** - Analiza opiniones de un profesor
3. **`curso --name "Nombre"`** - Analiza opiniones de un curso
4. **`stats`** - Muestra estadísticas

---

## 🔧 Comandos Frecuentes

### Desarrollo
```bash
# Activar venv (SIEMPRE primero)
source venv/bin/activate

# Ejecutar CLI
python -m src.cli analizar
python -m src.cli profesor --id 123
python -m src.cli curso --name "Estructura de Datos"
python -m src.cli stats
```

### Entorno Virtual Python (venv)

**CRÍTICO**: SIEMPRE usar el entorno virtual.

```bash
# Crear venv (primera vez)
python3 -m venv venv

# Activar
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

---

**Última actualización**: 2025-11-23  
**Versión del proyecto**: 1.1.0  
**Mantenedores**: Equipo SentimentInsightUAM - UAM Azcapotzalco
