# 🏀 NBA COMBO PROPS ANALYZER - ANÁLISIS ESTADÍSTICO PROFESIONAL

## 🎯 NUEVAS CARACTERÍSTICAS AVANZADAS (v2.0)

Este script ahora funciona como un **agente profesional de análisis estadístico NBA** con métricas avanzadas y análisis predictivo mejorado.

---

## 📊 MÉTRICAS AVANZADAS IMPLEMENTADAS

### 1. **Promedio Ponderado (Weighted Average)**
- **Qué es**: Promedio que da más peso a los juegos recientes
- **Cómo funciona**:
  - Últimos 3 juegos: 60% del peso total (20% cada uno)
  - Primeros 3 juegos: 40% del peso total (13.33% cada uno)
- **Por qué es mejor**: Los juegos recientes reflejan mejor la forma actual del jugador
- **Ejemplo**:
  ```
  Juego 1 (más reciente): 35 pts+ast × 20% = 7.0
  Juego 2: 32 pts+ast × 20% = 6.4
  Juego 3: 38 pts+ast × 20% = 7.6
  Juego 4: 28 pts+ast × 13.33% = 3.73
  Juego 5: 30 pts+ast × 13.33% = 4.0
  Juego 6: 25 pts+ast × 13.33% = 3.33
  ────────────────────────────────────
  Weighted Average = 32.06 (vs Simple Average: 31.33)
  ```

### 2. **Análisis de Consistencia (Consistency Score)**
- **Qué mide**: Qué tan consistente es el rendimiento del jugador
- **Métrica usada**: Desviación Estándar + Coeficiente de Variación (CV)
- **Escala de Consistencia**:
  - **90-100**: VERY CONSISTENT (CV < 15%) - Jugador ultra confiable
  - **75-89**: CONSISTENT (CV 15-25%) - Confiable para props
  - **60-74**: MODERATE (CV 25-35%) - Usar con precaución
  - **40-59**: INCONSISTENT (CV 35-50%) - Alto riesgo
  - **0-39**: VERY INCONSISTENT (CV > 50%) - Evitar

- **Por qué importa**: Un jugador con alto promedio pero baja consistencia es más riesgoso que uno con promedio moderado pero alta consistencia

- **Ejemplo**:
  ```
  Jugador A: 30, 32, 31, 29, 33, 30 → STD: 1.47 → CV: 4.8% → Score: 95.2 (VERY CONSISTENT)
  Jugador B: 40, 20, 35, 18, 42, 25 → STD: 10.21 → CV: 36% → Score: 24 (INCONSISTENT)

  Ambos promedian ~30, pero Jugador A es mucho más confiable!
  ```

### 3. **Nivel de Confianza (Confidence Level)**
- **Sistema de Puntos** (máximo 100 puntos):

  **Factor 1: Distancia de la Línea (30 puntos máx)**
  - Diferencia ≥ 5 puntos: 30 pts
  - Diferencia ≥ 3 puntos: 20 pts
  - Diferencia ≥ 1.5 puntos: 10 pts

  **Factor 2: Hit Rate (30 puntos máx)**
  - Hit rate ≥ 83.3% (5/6): 30 pts
  - Hit rate ≥ 66.7% (4/6): 20 pts
  - Hit rate ≥ 50% (3/6): 10 pts

  **Factor 3: Consistencia (25 puntos máx)**
  - Consistency ≥ 85: 25 pts
  - Consistency ≥ 70: 18 pts
  - Consistency ≥ 55: 10 pts

  **Factor 4: Tendencia (15 puntos máx)**
  - Tendencia favorable (↑ para OVER o ↓ para UNDER): 15 pts
  - Tendencia estable (→): 8 pts

- **Niveles de Confianza**:
  - **80-100 pts**: VERY HIGH ⭐⭐⭐ - Apuesta fuerte
  - **60-79 pts**: HIGH ⭐⭐ - Buena apuesta
  - **40-59 pts**: MEDIUM ⭐ - Apuesta moderada
  - **20-39 pts**: LOW ○ - Apuesta arriesgada
  - **0-19 pts**: VERY LOW ○ - Evitar

### 4. **Recomendación Mejorada (Enhanced Recommendation)**
- Combina TODOS los factores anteriores
- Solo marca OVER ⭐⭐⭐ o UNDER ⭐⭐⭐ cuando la confianza es ALTA o MUY ALTA
- Usa el promedio ponderado (no el simple) para decisiones
- Considera consistencia como factor de riesgo

---

## 📈 COMPARACIÓN: ANTES vs AHORA

### ANTES (Versión Básica):
```
ANÁLISIS:
• Average: 31.5 vs Line 25.5: +6.0
• Hit Rate: 5/6 OVER (83.3%)
• Trend: ↑ IMPROVING
• RECOMMENDATION: OVER ⭐
```

### AHORA (Versión Profesional):
```
PROFESSIONAL STATISTICAL ANALYSIS:

📊 AVERAGES:
• Simple Average: 31.5 vs Line (25.5): +6.0
• Weighted Average (Recent Games Priority): 32.8 vs Line: +7.3
• Home/Away Split: Home 3G (avg 33.7) | Away 3G (avg 29.3)

📈 PERFORMANCE METRICS:
• Hit Rate: 5/6 games OVER (83.3%)
• Trend: ↑ IMPROVING (Last 3 vs First 3: +4.2)
• Standard Deviation: 2.8

🎯 CONSISTENCY ANALYSIS:
• Consistency Score: 91.2/100
• Rating: VERY CONSISTENT
• Very reliable performer

💪 CONFIDENCE LEVEL: VERY HIGH ⭐⭐⭐
• Confidence Score: 88/100
  ✓ Strong edge: +7.3 from line
  ✓ Excellent hit rate: 83.3%
  ✓ Very consistent performer
  ✓ Trending up (favorable)

🎲 FINAL RECOMMENDATION: OVER ⭐⭐⭐
```

---

## 🎲 CÓMO INTERPRETAR LOS RESULTADOS

### Ejemplo de Jugador IDEAL para Apostar:
```
✓ Weighted Average muy por encima de la línea (+5 o más)
✓ Consistency Score > 85 (muy consistente)
✓ Hit Rate > 80% (casi siempre supera la línea)
✓ Tendencia favorable (↑ si OVER, ↓ si UNDER)
✓ Confidence Level: VERY HIGH ⭐⭐⭐
→ APUESTA FUERTE
```

### Ejemplo de Jugador RIESGOSO:
```
⚠ Weighted Average cerca de la línea (-1 a +1)
⚠ Consistency Score < 60 (inconsistente)
⚠ Hit Rate 50% (a veces sí, a veces no)
⚠ Tendencia desfavorable
⚠ Confidence Level: LOW ○
→ EVITAR o apostar MUY POCO
```

### Ejemplo de Jugador MODERADO:
```
~ Weighted Average moderadamente sobre línea (+2 a +4)
~ Consistency Score 70-80 (decente)
~ Hit Rate 66% (2 de cada 3)
~ Tendencia estable (→)
~ Confidence Level: MEDIUM ⭐
→ APUESTA MODERADA
```

---

## 🔬 FÓRMULAS MATEMÁTICAS UTILIZADAS

### 1. Promedio Ponderado
```python
Weighted_Avg = Σ(value_i × weight_i) / Σ(weight_i)

Donde:
- value_i = valor del juego i
- weight_i = peso asignado al juego i
- Últimos 3 juegos: weight = 0.20 cada uno
- Primeros 3 juegos: weight = 0.1333 cada uno
```

### 2. Desviación Estándar
```python
σ = sqrt(Σ(x_i - μ)² / (n - 1))

Donde:
- σ = desviación estándar
- x_i = valor individual
- μ = media
- n = número de valores
```

### 3. Coeficiente de Variación
```python
CV = (σ / μ) × 100

Donde:
- CV = coeficiente de variación (%)
- σ = desviación estándar
- μ = media
```

### 4. Consistency Score
```python
Si CV < 15:   Score = 100 - CV        (Muy Consistente)
Si CV < 25:   Score = 90 - CV         (Consistente)
Si CV < 35:   Score = 75 - CV         (Moderado)
Si CV < 50:   Score = 60 - CV         (Inconsistente)
Si CV ≥ 50:   Score = max(0, 50 - CV) (Muy Inconsistente)
```

---

## 📊 EXCEL REPORT - NUEVAS COLUMNAS

### Summary Sheet:
| Column | Descripción |
|--------|-------------|
| **Player** | Nombre del jugador |
| **Team** | Equipo |
| **Weighted Avg** | Promedio ponderado (últimos juegos pesan más) |
| **Line** | Línea de la casa de apuestas |
| **Diff** | Diferencia (Weighted Avg - Line) |
| **Hit Rate** | % de veces que superó la línea |
| **Consistency** | Score de consistencia + rating |
| **Confidence** | Nivel de confianza + estrellas |
| **Recommendation** | Recomendación mejorada con estrellas |

### Individual Sheets:
Ahora incluyen sección expandida de **PROFESSIONAL STATISTICAL ANALYSIS** con:
- Promedios simples y ponderados
- Métricas de rendimiento
- Análisis de consistencia
- Nivel de confianza con factores
- Recomendación final mejorada

---

## 🎯 VENTAJAS DEL SISTEMA PROFESIONAL

### ✅ Más Precisión
- Usa promedio ponderado que refleja mejor la forma actual
- Considera consistencia como factor de riesgo

### ✅ Menos Riesgo
- Identifica jugadores volátiles (inconsistentes)
- Sistema de confianza multi-factor

### ✅ Mejor Toma de Decisiones
- Scoring objetivo (0-100 puntos)
- Factores claramente explicados
- Estrellas visuales (⭐⭐⭐) para decisiones rápidas

### ✅ Análisis Profesional
- Fórmulas estadísticas estándar de la industria
- Métricas usadas por analistas profesionales
- Presentación clara y profesional

---

## 💡 CONSEJOS PRO

### 1. **Prioriza Consistency Score**
Un jugador con Average alto pero Consistency baja puede tener un juego malo justo hoy. Busca Consistency > 70.

### 2. **Confía en VERY HIGH ⭐⭐⭐**
Cuando ves VERY HIGH con 3 estrellas, todos los factores están alineados. Alta probabilidad de éxito.

### 3. **Usa Weighted Average**
El weighted average es más predictivo que el simple average porque los juegos recientes pesan más.

### 4. **Combina con tu Análisis**
Usa esto como base estadística, pero también considera:
- Lesiones recientes
- Cambios en el lineup
- Matchup específico (defensa del oponente)
- Motivación del equipo

### 5. **Evita LOW Confidence**
Si el Confidence Level es LOW, generalmente hay mejores opciones disponibles.

---

## 🔄 COMPARACIÓN CON ANÁLISIS BÁSICO

| Métrica | Análisis Básico | Análisis Profesional |
|---------|----------------|---------------------|
| Promedio | Simple (todos los juegos igual) | Ponderado (recientes pesan más) |
| Riesgo | No considerado | Consistency Score |
| Confianza | Subjetivo | Sistema de puntos objetivo (0-100) |
| Factores | 2-3 factores | 4+ factores integrados |
| Decisión | OVER/UNDER genérico | Nivel de confianza con estrellas |
| Presentación | Básica | Profesional con emojis y secciones |

---

## 📚 EJEMPLO COMPLETO: CASO DE USO REAL

### Jugador: Tyler Herro
### Categoría: Points + Assists
### Línea: 25.5

#### Últimos 6 Juegos:
| Juego | PTS+AST | vs Line |
|-------|---------|---------|
| 1 | 35 | OVER |
| 2 | 27 | OVER |
| 3 | 39 | OVER |
| 4 | 23 | UNDER |
| 5 | 32 | OVER |
| 6 | 33 | OVER |

#### Análisis Profesional:

**Promedios:**
- Simple Average: 31.5
- Weighted Average: 32.8 (últimos juegos son mejores!)

**Consistencia:**
- Standard Deviation: 5.8
- Coefficient of Variation: 18.4%
- Consistency Score: 71.6/100
- Rating: CONSISTENT ✓

**Rendimiento:**
- Hit Rate: 5/6 (83.3%)
- Trend: ↑ IMPROVING (últimos 3 avg: 33.7 vs primeros 3 avg: 29.3)

**Confidence Score:**
- Distancia de línea: +7.3 → 30 pts
- Hit rate 83%: → 30 pts
- Consistency 71.6: → 18 pts
- Trend favorable: → 15 pts
- **TOTAL: 93/100** → VERY HIGH ⭐⭐⭐

**Recomendación Final:** OVER ⭐⭐⭐

**Interpretación:**
Este es un EXCELENTE pick! Tyler Herro está:
- Promediando 7+ puntos sobre la línea (ponderado)
- Muy consistente en este nivel (71.6 consistency)
- 83% de hit rate (solo 1 juego bajo)
- Tendencia positiva (mejorando)
- Confianza MUY ALTA (93/100)

→ **APUESTA FUERTE RECOMENDADA**

---

## 🚀 USO DEL SCRIPT

```bash
# Instalar dependencias (si no lo has hecho)
pip install pandas requests beautifulsoup4 openpyxl lxml

# Ejecutar análisis profesional
python nba_combo_props_analyzer.py
```

El script generará un Excel con TODAS estas métricas avanzadas automáticamente!

---

**¡Apuesta de forma más inteligente con análisis estadístico profesional!** 📊🏀💰
