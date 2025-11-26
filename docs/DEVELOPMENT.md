# Guía de Desarrollo - SentimentInsightUAM_SA

Guía para desarrolladores que quieren contribuir o extender el módulo de análisis de sentimientos.

---

## 📋 Índice

- [Entorno de Desarrollo](#entorno-de-desarrollo)
- [Estructura del Código](#estructura-del-código)
- [Convenciones](#convenciones)
- [Agregar Nuevas Funcionalidades](#agregar-nuevas-funcionalidades)
- [Testing](#testing)
- [Debugging](#debugging)

---

## Entorno de Desarrollo

### Configuración Inicial

```bash
# Clonar y configurar
git clone https://github.com/christianpm-gh/SentimentInsightUAM_SA.git
cd SentimentInsightUAM_SA

# Crear y activar venv
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
```

### Activar Siempre el Entorno

```bash
# SIEMPRE antes de trabajar
source venv/bin/activate

# Verificar
which python
# Debe mostrar: .../SentimentInsightUAM_SA/venv/bin/python
```

### Ejecutar CLI

```bash
# Formato
python -m src.cli [comando] [opciones]

# Ejemplos
python -m src.cli analizar --limit 10
python -m src.cli profesor --id 36
python -m src.cli stats
```

---

## Estructura del Código

```
src/
├── __init__.py           # Versión y metadata
├── cli.py                # CLI principal
├── core/                 # Utilidades core
│   └── __init__.py
├── db/                   # Capa de datos
│   ├── __init__.py       # Conexiones a BD
│   ├── models.py         # Modelos ORM
│   └── repository.py     # Consultas y actualizaciones
└── ml/                   # Capa de ML
    ├── __init__.py       # SentimentAnalyzer
    ├── categorizer.py    # OpinionCategorizer
    └── processor.py      # OpinionProcessor
```

### Responsabilidades por Módulo

| Módulo | Archivo | Responsabilidad |
|--------|---------|-----------------|
| CLI | `cli.py` | Parseo de argumentos, orquestación |
| DB | `db/__init__.py` | Conexiones PostgreSQL + MongoDB |
| DB | `db/models.py` | Modelos ORM SQLAlchemy |
| DB | `db/repository.py` | Queries y updates |
| ML | `ml/__init__.py` | Análisis BERT |
| ML | `ml/categorizer.py` | Categorización por aspectos |
| ML | `ml/processor.py` | Flujo de procesamiento |

---

## Convenciones

### Estilo de Código

```python
# Imports ordenados
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Type hints obligatorios
async def analizar_texto(texto: str) -> Dict[str, Any]:
    ...

# Docstrings en funciones públicas
async def procesar_opinion(opinion_id: str) -> bool:
    """
    Procesa una opinión individual.
    
    Args:
        opinion_id: ID de MongoDB de la opinión
    
    Returns:
        True si el procesamiento fue exitoso
    
    Raises:
        ValueError: Si el ID es inválido
    """
    ...
```

### Nombres

| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| Archivos | snake_case | `opinion_processor.py` |
| Clases | PascalCase | `SentimentAnalyzer` |
| Funciones | snake_case | `analizar_batch` |
| Constantes | UPPER_SNAKE | `BATCH_SIZE` |
| Variables | snake_case | `resultado_analisis` |

### Commits

Seguir [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat: añade nuevo método de categorización
fix: corrige mapeo de etiquetas BERT
docs: actualiza documentación de API
refactor: simplifica lógica de OpinionProcessor
test: añade tests para SentimentAnalyzer
```

---

## Agregar Nuevas Funcionalidades

### Ejemplo: Nuevo Comando CLI

```python
# En cli.py

# 1. Definir función async
async def comando_nuevo(args):
    """
    Nuevo comando personalizado.
    """
    await init_all_databases()
    try:
        # Lógica aquí
        pass
    finally:
        await close_all_databases()

# 2. Agregar subparser en main()
parser_nuevo = subparsers.add_parser(
    'nuevo',
    help='Descripción del nuevo comando'
)
parser_nuevo.add_argument(
    '--opcion',
    type=str,
    help='Descripción de la opción'
)

# 3. Agregar case en el switch
elif args.comando == 'nuevo':
    asyncio.run(comando_nuevo(args))
```

### Ejemplo: Nueva Función de Repositorio

```python
# En db/repository.py

async def obtener_opiniones_por_fecha(
    fecha_inicio: datetime,
    fecha_fin: datetime,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Obtiene opiniones en un rango de fechas.
    
    Args:
        fecha_inicio: Fecha inicial
        fecha_fin: Fecha final
        limit: Máximo de resultados
    
    Returns:
        Lista de documentos de opiniones
    """
    db = get_mongo_db()
    
    cursor = db.opiniones.find({
        "fecha": {
            "$gte": fecha_inicio,
            "$lte": fecha_fin
        }
    }).limit(limit)
    
    return await cursor.to_list(length=limit)
```

### Ejemplo: Nuevo Aspecto de Categorización

```python
# En ml/categorizer.py

class OpinionCategorizer:
    
    KEYWORDS = {
        # Aspectos existentes...
        
        # Nuevo aspecto
        "puntualidad": {
            "positivo": [
                "puntual", "a tiempo", "respeta horario",
                "nunca falta", "siempre llega"
            ],
            "negativo": [
                "impuntual", "llega tarde", "falta mucho",
                "cancela clases", "no respeta horario"
            ]
        }
    }
```

---

## Testing

### Estructura de Tests

```
tests/
├── __init__.py
├── conftest.py           # Fixtures compartidos
├── test_cli.py           # Tests de CLI
├── test_analyzer.py      # Tests de SentimentAnalyzer
├── test_categorizer.py   # Tests de OpinionCategorizer
└── test_repository.py    # Tests de repository
```

### Ejemplo de Test

```python
# tests/test_analyzer.py
import pytest
from src.ml import SentimentAnalyzer, SentimentResult

@pytest.fixture
def analyzer():
    return SentimentAnalyzer()

def test_analizar_texto_positivo(analyzer):
    resultado = analyzer.analizar("Excelente profesor, muy claro")
    assert resultado.clasificacion == "positivo"
    assert resultado.confianza > 0.8

def test_analizar_texto_negativo(analyzer):
    resultado = analyzer.analizar("Muy mal profesor, no explica nada")
    assert resultado.clasificacion == "negativo"
    assert resultado.confianza > 0.8

def test_analizar_batch(analyzer):
    textos = [
        "Buen profesor",
        "Malo el profesor"
    ]
    resultados = analyzer.analizar_batch(textos)
    assert len(resultados) == 2
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con coverage
pytest --cov=src

# Test específico
pytest tests/test_analyzer.py -v
```

---

## Debugging

### Logging

```python
import logging

# Configurar nivel
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Usar
logger.debug("Mensaje de debug")
logger.info("Mensaje informativo")
logger.error("Mensaje de error")
```

### Variables de Entorno para Debug

```env
LOG_LEVEL=DEBUG
DEBUG=true
```

### Inspeccionar Datos de MongoDB

```bash
# Script de verificación
python scripts/verificar_mongo.py

# O usar mongosh directamente
docker exec -it sentiment_mongo mongosh -u sentiment_admin -p dev_password_2024 --authenticationDatabase sentiment_uam_nlp
```

```javascript
// En mongosh
use sentiment_uam_nlp
db.opiniones.findOne({profesor_id: 36})
db.opiniones.countDocuments({"sentimiento_general.analizado": true})
```

### Debugging del Analizador

```python
# Script de prueba rápida
import asyncio
from src.ml import get_analyzer

def test_analyzer():
    analyzer = get_analyzer()
    analyzer.load_model()
    
    texto = "Muy buen profesor, explica claramente"
    resultado = analyzer.analizar(texto)
    
    print(f"Texto: {texto}")
    print(f"Clasificación: {resultado.clasificacion}")
    print(f"Confianza: {resultado.confianza}")
    print(f"Pesos: {resultado.pesos}")

if __name__ == "__main__":
    test_analyzer()
```

### Debugging de Conexiones

```python
# Script de verificación de conexiones
import asyncio
from src.db import init_all_databases, close_all_databases

async def test_connections():
    try:
        await init_all_databases()
        print("✓ Conexiones exitosas")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await close_all_databases()

asyncio.run(test_connections())
```

---

## Herramientas Recomendadas

### Editor/IDE

- **VS Code** con extensiones:
  - Python
  - Pylance
  - Python Docstring Generator

### Linting

```bash
# Instalar
pip install pylint flake8 black

# Ejecutar
pylint src/
flake8 src/
black src/ --check
```

### Formateo

```bash
# Formatear código
black src/
```

---

## Recursos

- [Documentación HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Motor (MongoDB async)](https://motor.readthedocs.io/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

---

**Última actualización**: 2025-11-26  
**Versión**: 1.1.0
