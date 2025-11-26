# Contribuir a SentimentInsightUAM_SA

¡Gracias por tu interés en contribuir al proyecto! Este documento describe las guías y convenciones para contribuir al módulo de análisis de sentimientos.

---

## 📋 Índice

- [Código de Conducta](#código-de-conducta)
- [Cómo Contribuir](#cómo-contribuir)
- [Configuración del Entorno](#configuración-del-entorno)
- [Convenciones de Código](#convenciones-de-código)
- [Proceso de Pull Request](#proceso-de-pull-request)
- [Reportar Bugs](#reportar-bugs)
- [Solicitar Funcionalidades](#solicitar-funcionalidades)

---

## Código de Conducta

Este proyecto es parte de un esfuerzo educativo de la UAM Azcapotzalco. Esperamos que todos los contribuidores:

- Sean respetuosos y constructivos en sus comentarios
- Acepten críticas constructivas de manera profesional
- Se enfoquen en lo mejor para el proyecto
- Muestren empatía hacia otros miembros de la comunidad

---

## Cómo Contribuir

### 1. Fork y Clone

```bash
# Fork el repositorio desde GitHub
# Clone tu fork
git clone https://github.com/TU_USUARIO/SentimentInsightUAM_SA.git
cd SentimentInsightUAM_SA

# Añade el repositorio original como upstream
git remote add upstream https://github.com/christianpm-gh/SentimentInsightUAM_SA.git
```

### 2. Crear una Rama

```bash
# Actualiza tu main
git checkout main
git pull upstream main

# Crea una rama para tu contribución
git checkout -b feature/nombre-descriptivo
# o
git checkout -b fix/descripcion-del-bug
```

### 3. Hacer Cambios

- Sigue las [convenciones de código](#convenciones-de-código)
- Añade tests si es aplicable
- Actualiza la documentación si es necesario

### 4. Commit y Push

```bash
# Añade tus cambios
git add .

# Commit con mensaje descriptivo
git commit -m "feat: añade análisis por aspectos adicionales"

# Push a tu fork
git push origin feature/nombre-descriptivo
```

### 5. Crear Pull Request

- Abre un PR desde tu fork hacia el repositorio original
- Describe claramente los cambios realizados
- Referencia cualquier issue relacionado

---

## Configuración del Entorno

### Prerrequisitos

- Python 3.11+
- Docker (para bases de datos)
- Git

### Instalación para Desarrollo

```bash
# 1. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
```

### Bases de Datos

Las bases de datos deben estar corriendo desde el proyecto principal:

```bash
cd ~/dev/python-dev/SentimentInsightUAM
docker-compose up -d
```

### Verificación

```bash
# Verificar que todo funciona
python -m src.cli stats
```

---

## Convenciones de Código

### Estilo Python

- **PEP 8**: Seguir las guías de estilo de Python
- **Type Hints**: Usar anotaciones de tipo en funciones
- **Docstrings**: Documentar funciones y clases con docstrings

```python
async def analizar_opinion(texto: str) -> Dict[str, Any]:
    """
    Analiza el sentimiento de una opinión.
    
    Args:
        texto: Texto de la opinión a analizar
    
    Returns:
        Diccionario con clasificación, pesos y confianza
    
    Raises:
        ValueError: Si el texto está vacío
    """
    ...
```

### Estructura de Archivos

```
src/
├── module/
│   ├── __init__.py      # Exports públicos
│   ├── service.py       # Lógica de negocio
│   └── models.py        # Modelos de datos
```

### Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

| Tipo | Descripción |
|------|-------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `style` | Formato (no afecta código) |
| `refactor` | Refactorización de código |
| `test` | Añadir o modificar tests |
| `chore` | Tareas de mantenimiento |

Ejemplos:
```
feat: añade categorización por empatía
fix: corrige mapeo de etiquetas BERT
docs: actualiza README con nuevos comandos
refactor: simplifica lógica de OpinionProcessor
```

### Nombres

| Elemento | Convención | Ejemplo |
|----------|------------|---------|
| Archivos | snake_case | `opinion_processor.py` |
| Clases | PascalCase | `SentimentAnalyzer` |
| Funciones | snake_case | `analizar_batch` |
| Constantes | UPPER_SNAKE | `BATCH_SIZE` |
| Variables | snake_case | `resultado_analisis` |

---

## Proceso de Pull Request

### Checklist

Antes de crear un PR, asegúrate de:

- [ ] El código sigue las convenciones del proyecto
- [ ] Has probado los cambios localmente
- [ ] La documentación está actualizada (si aplica)
- [ ] Los commits siguen la convención de mensajes
- [ ] No hay conflictos con la rama `main`

### Descripción del PR

Incluye en la descripción:

1. **Qué**: Descripción clara del cambio
2. **Por qué**: Motivación del cambio
3. **Cómo**: Breve explicación técnica
4. **Tests**: Cómo probaste el cambio

### Revisión

- Un mantenedor revisará tu PR
- Puede haber comentarios o solicitudes de cambios
- Una vez aprobado, se hará merge a `main`

---

## Reportar Bugs

### Antes de Reportar

1. Verifica que el bug no haya sido reportado ya
2. Asegúrate de estar en la versión más reciente
3. Confirma que las bases de datos están corriendo

### Información a Incluir

```markdown
## Descripción del Bug
Descripción clara del problema.

## Pasos para Reproducir
1. Ejecutar '...'
2. Observar '...'

## Comportamiento Esperado
Qué debería pasar.

## Comportamiento Actual
Qué está pasando realmente.

## Entorno
- OS: macOS/Linux/Windows
- Python: 3.11.x
- Versión del proyecto: 1.1.0

## Logs
```
Pegar logs relevantes aquí
```
```

---

## Solicitar Funcionalidades

### Información a Incluir

1. **Problema**: Qué problema resuelve la funcionalidad
2. **Solución propuesta**: Cómo debería funcionar
3. **Alternativas**: Otras soluciones consideradas
4. **Contexto**: Información adicional relevante

---

## Recursos

- [Documentación del proyecto](docs/)
- [Guía de desarrollo](docs/DEVELOPMENT.md)
- [Arquitectura del sistema](docs/ARCHITECTURE.md)
- [Flujos críticos](docs/FLOWS.md)

---

## Contacto

Para preguntas sobre contribuciones, puedes:

- Abrir un issue con la etiqueta `question`
- Contactar al equipo de mantenimiento

---

**Gracias por contribuir a SentimentInsightUAM_SA!** 🎉
