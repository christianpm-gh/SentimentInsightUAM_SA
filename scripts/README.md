# Scripts de Consulta - SentimentInsightUAM_SA

Scripts útiles para consultar, visualizar y verificar análisis de sentimientos.

---

## 📋 Índice

- [Scripts Disponibles](#scripts-disponibles)
- [Flujo de Trabajo Típico](#flujo-de-trabajo-típico)
- [Requisitos](#requisitos)

---

## Scripts Disponibles

### 1. `listar_profesores.py`

Lista todos los profesores disponibles en la base de datos PostgreSQL.

```bash
# Listar primeros 20 profesores (default)
python scripts/listar_profesores.py

# Listar hasta 50 profesores
python scripts/listar_profesores.py --limit 50

# Filtrar por departamento
python scripts/listar_profesores.py --departamento Sistemas
```

**Salida ejemplo:**
```
ID     Nombre                                             Departamento   
--------------------------------------------------------------------------------
36     Josue Padilla - UAM (Azcapotzalco) ...            Sistemas       
42     María García - UAM (Azcapotzalco) ...             Sistemas       
```

---

### 2. `listar_materias.py`

Lista todas las materias/cursos con conteo de opiniones desde MongoDB.

```bash
# Listar primeras 20 materias (default)
python scripts/listar_materias.py

# Listar hasta 30 materias
python scripts/listar_materias.py --limit 30
```

**Salida ejemplo:**
```
#    Materia                                                    Opiniones
--------------------------------------------------------------------------------
1    Estructura de Datos                                              152
2    Programación Orientada a Objetos                                  98
3    Bases de Datos                                                    75
```

---

### 3. `analisis_profesor.py`

Muestra análisis completo con estadísticas detalladas de un profesor.

```bash
# Por ID de profesor
python scripts/analisis_profesor.py 36

# Por nombre (búsqueda parcial)
python scripts/analisis_profesor.py --nombre "Josue Padilla"
```

**Salida ejemplo:**
```
================================================================================
ANÁLISIS DE PROFESOR
================================================================================

ID: 36
Nombre: Josue Padilla - UAM (Azcapotzalco)
Departamento: Sistemas
Slug: josue-padilla

--------------------------------------------------------------------------------
ESTADÍSTICAS GENERALES
--------------------------------------------------------------------------------
Total de opiniones: 38
Sentimiento analizado: 38 (100.0%)
Categorización analizada: 38 (100.0%)

--------------------------------------------------------------------------------
DISTRIBUCIÓN DE SENTIMIENTOS
--------------------------------------------------------------------------------
Positivas:  22 (57.9%)
Neutrales:  14 (36.8%)
Negativas:   2 (5.3%)

--------------------------------------------------------------------------------
CATEGORIZACIÓN DETALLADA
--------------------------------------------------------------------------------
Calidad Didáctica:
  Positivo:  26 (68.4%)
  Neutral:   12 (31.6%)
  Negativo:   0 (0.0%)

Método de Evaluación:
  Positivo:   1 (2.6%)
  Neutral:   32 (84.2%)
  Negativo:   5 (13.2%)

Empatía:
  Positivo:  12 (31.6%)
  Neutral:   26 (68.4%)
  Negativo:   0 (0.0%)

--------------------------------------------------------------------------------
MUESTRA DE OPINIÓN
--------------------------------------------------------------------------------
"Muy buen profesor, domina la materia y sabe transmitir su conocimiento..."
Sentimiento: POSITIVO (confianza: 1.00)

================================================================================
```

---

### 4. `analisis_materia.py`

Muestra análisis completo con estadísticas de una materia/curso.

```bash
# Análisis de una materia
python scripts/analisis_materia.py "Estructura de Datos"

# Búsqueda parcial (encuentra "Programación I", "Programación II", etc.)
python scripts/analisis_materia.py "Programación"
```

**Salida ejemplo:**
```
================================================================================
ANÁLISIS DE MATERIA/CURSO
================================================================================

Materia: Estructura de Datos

--------------------------------------------------------------------------------
ESTADÍSTICAS GENERALES
--------------------------------------------------------------------------------
Total de opiniones: 152
Sentimiento analizado: 152 (100.0%)
Categorización analizada: 152 (100.0%)

--------------------------------------------------------------------------------
DISTRIBUCIÓN DE SENTIMIENTOS
--------------------------------------------------------------------------------
Positivas:  45 (29.6%)
Neutrales:  87 (57.2%)
Negativas:  20 (13.2%)

--------------------------------------------------------------------------------
PROFESORES QUE IMPARTEN LA MATERIA
--------------------------------------------------------------------------------
  • Josue Padilla (38 opiniones)
  • María García (42 opiniones)
  • ...
```

---

### 5. `ver_opinion.py`

Muestra detalles completos de una opinión específica por su ObjectId de MongoDB.

```bash
python scripts/ver_opinion.py 691160d0c45dc23d465370f4
```

**Salida ejemplo:**
```
================================================================================
DETALLES DE LA OPINIÓN
================================================================================

ID: 691160d0c45dc23d465370f4
Profesor: Josue Padilla (ID: 36)
Curso: Bases de Datos
Fecha: 2025-08-09 00:00:00

--------------------------------------------------------------------------------
COMENTARIO:
--------------------------------------------------------------------------------
Muy buen profesor, domina la materia y sabe transmitir su conocimiento...

--------------------------------------------------------------------------------
SENTIMIENTO GENERAL:
--------------------------------------------------------------------------------
Clasificación: POSITIVO
Confianza: 0.998
Pesos:
  - Positivo: 0.998
  - Neutral:  0.001
  - Negativo: 0.001
Modelo: finiteautomata/beto-sentiment-analysis-v1.0
Fecha análisis: 2025-11-23 21:53:18

--------------------------------------------------------------------------------
CATEGORIZACIÓN:
--------------------------------------------------------------------------------
Calidad Didáctica: POSITIVO
  Confianza: 1.000
  Palabras: domina, buen profesor, aprend, conocimiento, sabe

Método Evaluación: NEUTRAL
  Confianza: 0.500

Empatía: NEUTRAL
  Confianza: 0.500
Modelo: keyword-based-v1.0

================================================================================
```

---

### 6. `verificar_mongo.py`

Verifica la conexión a MongoDB y muestra documentos de ejemplo con análisis.

```bash
python scripts/verificar_mongo.py
```

**Salida ejemplo:**
```
================================================================================
VERIFICACIÓN DE DATOS EN MONGODB
================================================================================

--- Documento 1 (ID: ...) ---
Profesor ID: 36
Comentario: Muy buen profesor...

[Sentimiento General]
{'analizado': True, 'clasificacion': 'positivo', 'confianza': 0.998, ...}

[Categorización]
{'analizado': True, 'calidad_didactica': {...}, ...}

Se mostraron 3 documentos de muestra.
```

---

### 7. `procesar_categorizacion.py`

Procesa opiniones pendientes de categorización (sin sentimiento).

```bash
python scripts/procesar_categorizacion.py
```

---

## Flujo de Trabajo Típico

### 1. Explorar profesores disponibles

```bash
python scripts/listar_profesores.py --limit 50
```

### 2. Ver análisis de un profesor específico

```bash
python scripts/analisis_profesor.py 36
```

### 3. Explorar materias disponibles

```bash
python scripts/listar_materias.py --limit 30
```

### 4. Ver análisis de una materia

```bash
python scripts/analisis_materia.py "Estructura de Datos"
```

### 5. Ver detalles de una opinión específica

```bash
python scripts/ver_opinion.py 691160d0c45dc23d465370f4
```

### 6. Verificar datos en MongoDB

```bash
python scripts/verificar_mongo.py
```

---

## Requisitos

Antes de usar los scripts, asegúrate de:

1. **Activar el entorno virtual:**
   ```bash
   source venv/bin/activate
   ```

2. **Bases de datos corriendo:**
   ```bash
   # En el proyecto principal SentimentInsightUAM
   cd ~/dev/python-dev/SentimentInsightUAM
   docker-compose up -d
   ```

3. **Variables de entorno configuradas:**
   - Archivo `.env` debe existir con las credenciales correctas

---

## Notas

- Todos los scripts requieren que el entorno virtual esté activado
- Las bases de datos (PostgreSQL + MongoDB) deben estar corriendo
- Los scripts respetan la configuración del archivo `.env`
- Las búsquedas son case-insensitive (no distinguen mayúsculas/minúsculas)
- Los scripts usan la misma conexión async que el CLI principal

---

**Última actualización**: 2025-11-26  
**Versión**: 1.1.0
