# Fórmulas del Análisis de Sentimiento y Categorización

Este documento describe las fórmulas matemáticas y métodos utilizados en SentimentInsightUAM_SA para el análisis de opiniones de profesores.

---

## 📊 1. Análisis de Sentimiento General (BERT)

### 1.1 Modelo Base
Se utiliza un modelo BERT pre-entrenado para clasificación de secuencias:

- **Modelo por defecto**: `finiteautomata/beto-sentiment-analysis`
- **Arquitectura**: BERT con capa de clasificación de 3 clases

### 1.2 Clasificación Softmax

El modelo BERT produce logits que se transforman en probabilidades usando **softmax**:

$$
P(clase_i) = \frac{e^{z_i}}{\sum_{j=1}^{3} e^{z_j}}
$$

Donde:
- $z_i$ = logit de la clase $i$
- $P(clase_i)$ = probabilidad de la clase $i$ (positivo, neutral, negativo)

#### Propósito del Cálculo

El resultado del modelo BERT nos proporciona:

1. **Clasificación automática**: Determina si una opinión de un profesor es positiva, neutral o negativa sin intervención manual.

2. **Medición de confianza**: El score de confianza indica qué tan seguro está el modelo de su predicción, permitiendo identificar opiniones ambiguas que podrían requerir revisión manual.

3. **Distribución de probabilidades (pesos)**: Los pesos normalizados permiten:
   - Calcular estadísticas agregadas ponderadas por confianza
   - Generar visualizaciones de distribución de sentimientos
   - Identificar tendencias generales en las opiniones de profesores/cursos
   - Comparar la percepción entre diferentes profesores o materias

4. **Análisis temporal**: Al procesar opiniones con fechas, se pueden detectar cambios en la percepción de un profesor a lo largo del tiempo.

### 1.3 Cálculo de Pesos por Clase

Cuando el modelo retorna solo la clase ganadora y su confianza, los pesos se distribuyen así:

$$
peso_{ganador} = confianza
$$

$$
peso_{otros} = \frac{1 - confianza}{2}
$$

### 1.4 Normalización de Pesos

Los pesos se normalizan para sumar 1:

$$
peso_{normalizado_i} = \frac{peso_i}{\sum_{j} peso_j}
$$

---

## 🏷️ 2. Categorización por Palabras Clave

### 2.1 Sistema de Categorías

El categorizador clasifica opiniones en **tres dimensiones**:

| Categoría | Descripción |
|-----------|-------------|
| **Calidad Didáctica** | Evalúa habilidades de enseñanza, claridad, dominio del tema |
| **Método de Evaluación** | Evalúa justicia, dificultad, criterios de calificación |
| **Empatía** | Evalúa trato humano, accesibilidad, flexibilidad |

#### Propósito de la Categorización

La categorización por palabras clave permite:

1. **Análisis multidimensional**: A diferencia del sentimiento general, esta técnica desglosa la opinión en aspectos específicos del desempeño docente.

2. **Identificación de fortalezas/debilidades**: Un profesor puede tener alta calidad didáctica pero baja empatía, lo cual no se detectaría solo con sentimiento general.

3. **Retroalimentación específica**: Las instituciones pueden generar reportes detallados para mejorar áreas específicas.

4. **Comparación por dimensión**: Permite comparar profesores/cursos en cada dimensión independientemente.

### 2.2 Fórmula de Score por Categoría

Para cada categoría (calidad didáctica, método de evaluación, empatía), se realiza el siguiente proceso:

#### Paso 1: Conteo de Palabras Clave

Se buscan en el texto todas las palabras/frases del diccionario de palabras clave:

$$
n_{pos} = \sum_{i=1}^{k_{pos}} \mathbb{1}(palabra\_positiva_i \in texto)
$$

$$
n_{neg} = \sum_{i=1}^{k_{neg}} \mathbb{1}(palabra\_negativa_i \in texto)
$$

Donde:
- $n_{pos}$ = cantidad de palabras positivas encontradas
- $n_{neg}$ = cantidad de palabras negativas encontradas
- $k_{pos}$, $k_{neg}$ = tamaño de los diccionarios positivo y negativo
- $\mathbb{1}(\cdot)$ = función indicadora (1 si la condición es verdadera, 0 si no)

#### Paso 2: Cálculo del Total

$$
n_{total} = n_{pos} + n_{neg}
$$

### 2.3 Score Positivo

El score positivo representa la proporción de palabras positivas respecto al total encontrado:

$$
score_{positivo} = \frac{n_{pos}}{n_{total}} = \frac{n_{pos}}{n_{pos} + n_{neg}}
$$

Este score varía de 0 a 1:
- **score = 1.0**: Solo se encontraron palabras positivas
- **score = 0.5**: Balance entre palabras positivas y negativas
- **score = 0.0**: Solo se encontraron palabras negativas

### 2.4 Reglas de Clasificación

La valoración se determina según umbrales:

| Condición | Valoración | Confianza |
|-----------|------------|-----------|
| $score_{positivo} > 0.6$ | positivo | $score_{positivo}$ |
| $score_{positivo} < 0.4$ | negativo | $1 - score_{positivo}$ |
| $0.4 \leq score_{positivo} \leq 0.6$ | neutral | $0.5$ |
| $n_{total} = 0$ | neutral | $0.5$ |

### 2.5 Fórmula Combinada

La fórmula completa para determinar la valoración en cada categoría es:

$$
valoracion = 
\begin{cases}
\text{positivo} & \text{si } \frac{n_{pos}}{n_{total}} > 0.6 \\
\text{negativo} & \text{si } \frac{n_{pos}}{n_{total}} < 0.4 \\
\text{neutral} & \text{si } 0.4 \leq \frac{n_{pos}}{n_{total}} \leq 0.6 \\
\text{neutral} & \text{si } n_{total} = 0 \text{ (sin palabras clave)}
\end{cases}
$$

### 2.6 Cálculo de Confianza por Categoría

La confianza indica qué tan segura es la clasificación:

$$
confianza = 
\begin{cases}
score_{positivo} & \text{si valoración = positivo} \\
1 - score_{positivo} & \text{si valoración = negativo} \\
0.5 & \text{si valoración = neutral}
\end{cases}
$$

**Interpretación de la confianza**:
- **Alta confianza (>0.8)**: La opinión tiene palabras clave claramente predominantes en una dirección.
- **Confianza media (0.6-0.8)**: Predomina una polaridad pero hay presencia de la opuesta.
- **Confianza baja (0.5)**: Neutral por falta de palabras clave o balance exacto.

---

## ⏱️ 3. Métricas de Rendimiento

### 3.1 Tiempo de Procesamiento

Para procesamiento en batch:

$$
tiempo_{por\_texto} = \frac{tiempo_{total}}{n_{textos}}
$$

### 3.2 Tasa de Éxito

$$
tasa_{exito} = \frac{actualizaciones_{exitosas}}{opiniones_{procesadas}} \times 100\%
$$

---

## 🔢 4. Resumen de Variables

| Variable | Descripción | Rango |
|----------|-------------|-------|
| `clasificacion` | Clase predicha | positivo, neutral, negativo |
| `confianza` | Certeza del modelo | [0, 1] |
| `pesos` | Distribución de probabilidades | Suma = 1 |
| `score_positivo` | Ratio de palabras positivas | [0, 1] |
| `tiempo_ms` | Tiempo de procesamiento | milisegundos |

---

## 📝 Notas Técnicas

1. **Truncamiento BERT**: Los textos se truncan a 512 tokens (límite de BERT).
2. **Batch Processing**: Se procesan múltiples textos simultáneamente para eficiencia.
3. **Palabras Clave**: El categorizador usa ~200 palabras/frases por categoría en español mexicano.
4. **Dispositivos soportados**: CPU, CUDA (GPU NVIDIA), MPS (Apple Silicon).
5. **Diccionarios de palabras**: Cada categoría tiene diccionarios separados de palabras positivas y negativas específicas al contexto educativo universitario.
6. **Búsqueda de coincidencias**: La búsqueda de palabras clave es case-insensitive y busca subcadenas.

---

*Última actualización: 2025-12-03*  
*Versión: 1.1.0*
