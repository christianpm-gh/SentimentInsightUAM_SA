# Ejemplo de Salida - SentimentInsightUAM_SA

Este archivo muestra un ejemplo real de la salida del sistema de análisis de sentimientos.

---

## Análisis de Profesor (ID: 36)

```
================================================================================
ANÁLISIS DE PROFESOR
================================================================================

ID: 36
Nombre: Josue Padilla - UAM (Azcapotzalco) - Universidad Autónoma Metropolitana - MisProfesores.com
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
"Muy buen profesor, domina la materia y sabe transmitir su conocimiento. La carga de trabajo es bastante: actividades (algunas sorpresa), exámenes, proyecto final y revisiones presenciales. Recomendado..."
Sentimiento: POSITIVO (confianza: 1.00)


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
Muy buen profesor, domina la materia y sabe transmitir su conocimiento. La carga de trabajo es bastante: actividades (algunas sorpresa), exámenes, proyecto final y revisiones presenciales. Recomendado si quieres aprender bien

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
Fecha análisis: 2025-11-23 21:53:18.000000

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

## Interpretación de Resultados

### Sentimiento General
- **Clasificación**: La polaridad global de la opinión (POSITIVO/NEUTRAL/NEGATIVO)
- **Confianza**: Qué tan seguro está el modelo de su clasificación (0.0 a 1.0)
- **Pesos**: Probabilidades asignadas a cada clase

### Categorización por Aspectos
- **Calidad Didáctica**: Evalúa cómo enseña el profesor
- **Método de Evaluación**: Evalúa la forma de evaluar y dificultad
- **Empatía**: Evalúa el trato hacia los estudiantes

### Palabras Clave
Las palabras detectadas que influyeron en la categorización.

---

**Última actualización**: 2025-11-26  
**Versión**: 1.1.0