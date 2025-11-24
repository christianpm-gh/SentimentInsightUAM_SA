# Scripts de Consulta - SentimentInsightUAM_SA

Scripts útiles para consultar y visualizar análisis de sentimientos.

## 📋 Scripts Disponibles

### 1. `listar_profesores.py`
Lista todos los profesores disponibles en la base de datos.

**Uso:**
```bash
# Listar primeros 20 profesores
python scripts/listar_profesores.py

# Listar hasta 50 profesores
python scripts/listar_profesores.py --limit 50

# Filtrar por departamento
python scripts/listar_profesores.py --departamento Sistemas
```

**Salida:**
```
ID     Nombre                                             Departamento   
--------------------------------------------------------------------------------
36     Josue Padilla - UAM (Azcapotzalco) ...            Sistemas       
```

---

### 2. `listar_materias.py`
Lista todas las materias/cursos con conteo de opiniones.

**Uso:**
```bash
# Listar primeras 20 materias
python scripts/listar_materias.py

# Listar hasta 30 materias
python scripts/listar_materias.py --limit 30
```

**Salida:**
```
#    Materia                                                    Opiniones
--------------------------------------------------------------------------------
1    Estructura de Datos                                              152
2    Programación Orientada a Objetos                                 98
```

---

### 3. `ver_opinion.py`
Muestra detalles completos de una opinión específica.

**Uso:**
```bash
# Ver opinión por ObjectId
python scripts/ver_opinion.py 673007e1b8f26b8f63f9fb31
```

**Salida:**
```
================================================================================
DETALLES DE LA OPINIÓN
================================================================================

ID: 673007e1b8f26b8f63f9fb31
Profesor: Josue Padilla (ID: 36)
Curso: Estructura de Datos
Fecha: 2024-05-15

--------------------------------------------------------------------------------
COMENTARIO:
--------------------------------------------------------------------------------
Muy buen profesor, domina la materia y sabe transmitir...

--------------------------------------------------------------------------------
SENTIMIENTO GENERAL:
--------------------------------------------------------------------------------
Clasificación: NEUTRAL
Confianza: 0.348
Pesos:
  - Positivo: 0.326
  - Neutral:  0.348
  - Negativo: 0.326

--------------------------------------------------------------------------------
CATEGORIZACIÓN:
--------------------------------------------------------------------------------
Calidad Didáctica: POSITIVO
  Confianza: 1.000
  Palabras: domina, buen profesor, sabe, conocimiento

Método Evaluación: NEUTRAL
  Confianza: 0.500

Empatía: NEUTRAL
  Confianza: 0.500
```

---

### 4. `analisis_profesor.py`
Análisis completo con estadísticas de un profesor.

**Uso:**
```bash
# Por ID de profesor
python scripts/analisis_profesor.py 36

# Por nombre (búsqueda parcial)
python scripts/analisis_profesor.py --nombre "Josue Padilla"
```

**Salida:**
```
================================================================================
ANÁLISIS DE PROFESOR
================================================================================

ID: 36
Nombre: Josue Padilla - UAM (Azcapotzalco)
Departamento: Sistemas

--------------------------------------------------------------------------------
ESTADÍSTICAS GENERALES
--------------------------------------------------------------------------------
Total de opiniones: 38
Sentimiento analizado: 38 (100.0%)
Categorización analizada: 38 (100.0%)

--------------------------------------------------------------------------------
DISTRIBUCIÓN DE SENTIMIENTOS
--------------------------------------------------------------------------------
Positivas:  14 (36.8%)
Neutrales:  24 (63.2%)
Negativas:   0 (0.0%)

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
```

---

### 5. `analisis_materia.py`
Análisis completo con estadísticas de una materia/curso.

**Uso:**
```bash
# Análisis de una materia
python scripts/analisis_materia.py "Estructura de Datos"

# Búsqueda parcial (encuentra "Programación I", "Programación II", etc.)
python scripts/analisis_materia.py "Programación"
```

**Salida:**
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
  ...
```

---

## 🚀 Flujo de Trabajo Típico

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
python scripts/ver_opinion.py 673007e1b8f26b8f63f9fb31
```

---

## 📝 Notas

- Todos los scripts requieren que el entorno virtual esté activado
- Las bases de datos (PostgreSQL + MongoDB) deben estar corriendo
- Los scripts respetan la configuración del archivo `.env`
- Las búsquedas son case-insensitive (no distinguen mayúsculas/minúsculas)

---

## 🔧 Requisitos

Antes de usar los scripts, asegúrate de:

1. **Activar el entorno virtual:**
   ```bash
   source venv/bin/activate
   ```

2. **Bases de datos corriendo:**
   ```bash
   # En el proyecto principal SentimentInsightUAM
   docker-compose up -d
   ```

3. **Variables de entorno configuradas:**
   - Archivo `.env` debe existir con las credenciales correctas

---

**Última actualización:** 2025-11-09  
**Versión:** 1.0.0
