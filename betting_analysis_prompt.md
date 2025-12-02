# 🏀 PROMPT DE ANÁLISIS DE APUESTAS NBA - OVER/UNDER DE JUGADORES

## OBJETIVO
Analizar las estadísticas históricas de los últimos 5 juegos de jugadores NBA para generar recomendaciones precisas de **OVER/UNDER** en las siguientes categorías:
- **Puntos (PTS)**
- **Rebotes (REB)**
- **Asistencias (AST)**

---

## CONTEXTO Y DATOS DISPONIBLES

Los datos provienen de scrapers automatizados que extraen información de ESPN API y contienen:

### Datos por Jugador (Últimos 5 Juegos):
- **Estadísticas por Quarter**: PTS_Q1, PTS_Q2, PTS_Q3, PTS_Q4
- **Estadísticas Totales**: PTS_TOTAL, REB_TOTAL, AST_TOTAL, 3PM_TOTAL
- **Información del Partido**: Fecha, Oponente, Resultado (W/L), Local/Visitante
- **Minutos Jugados**: MIN

### Formato de Datos de Entrada:
```csv
PLAYER,TEAM,DATE,OPP,RESULT,HOME_AWAY,MIN,PTS_Q1,PTS_Q2,PTS_Q3,PTS_Q4,PTS_TOTAL,REB_Q1,REB_Q2,REB_Q3,REB_Q4,REB_TOTAL,AST_Q1,AST_Q2,AST_Q3,AST_Q4,AST_TOTAL,3PM_Q1,3PM_Q2,3PM_Q3,3PM_Q4,3PM_TOTAL
```

---

## METODOLOGÍA DE ANÁLISIS

### 1. ANÁLISIS DE TENDENCIAS Y CONSISTENCIA

Para cada jugador y métrica (PTS, REB, AST), calcular:

#### A. Métricas Estadísticas Básicas:
- **Promedio (μ)**: Media de los últimos 5 juegos
- **Desviación Estándar (σ)**: Medida de variabilidad
- **Coeficiente de Variación (CV)**: σ/μ × 100 (%)
  - CV < 15%: **MUY CONSISTENTE** ✅
  - CV 15-25%: **MODERADAMENTE CONSISTENTE** ⚠️
  - CV > 25%: **INCONSISTENTE** ❌

#### B. Tendencias Temporales:
- **Tendencia Reciente**: ¿Los últimos 2-3 juegos muestran mejora o declive?
- **Partidos en Casa vs Visitante**: Diferencia de rendimiento
- **Vs Oponentes Fuertes/Débiles**: Análisis de contexto defensivo

#### C. Análisis de Quarters:
- **Inicio de Juego (Q1+Q2)**: ¿El jugador empieza fuerte?
- **Cierre de Juego (Q3+Q4)**: ¿Es clutch en el 4to quarter?
- **Distribución de Carga**: ¿Consistente en todos los quarters o concentrado?

#### D. Correlaciones y Contexto:
- **Minutos Jugados**: ¿Hay correlación con rendimiento?
- **Resultados del Equipo (W/L)**: ¿Mejor en victorias o derrotas?
- **Descanso entre Partidos**: ¿Fatiga o frescura?

---

### 2. DETERMINACIÓN DE LÍNEAS DE OVER/UNDER

Para cada jugador, generar líneas de apuestas basadas en:

#### Fórmula de Línea Base:
```
Línea Over/Under = μ (Promedio) ± (0.5 × σ)
```

#### Ajustes según Contexto:

**Ajuste +1 a +3 puntos** (para OVER):
- Jugador juega en CASA
- Oponente tiene defensa débil (Top 25-30 de la liga)
- Jugador en racha (3+ juegos consecutivos sobre promedio)
- Aumento de minutos proyectados (compañero lesionado)

**Ajuste -1 a -3 puntos** (para UNDER):
- Jugador juega de VISITANTE
- Oponente tiene defensa élite (Top 5 de la liga)
- Jugador en mala racha (3+ juegos bajo promedio)
- Reducción de minutos proyectados (regreso de compañero)

---

### 3. GENERACIÓN DE RECOMENDACIONES

Para cada jugador, generar:

#### Formato de Salida:

```
🏀 JUGADOR: [Nombre del Jugador] ([Equipo])
📅 Partido de HOY: [Equipo] vs [Oponente] | [Local/Visitante] | [Hora]

─────────────────────────────────────────────────────────────

📊 PUNTOS (PTS)
   Promedio últimos 5: [μ] pts
   Desviación estándar: [σ] pts
   Rango típico: [[μ-σ], [μ+σ]] pts
   Consistencia: [CV]% - [MUY/MODERADAMENTE/IN]CONSISTENTE

   🎯 LÍNEA RECOMENDADA: [X.5] puntos

   📈 RECOMENDACIÓN: OVER / UNDER
   🔥 Confianza: ⭐⭐⭐⭐⭐ (1-5 estrellas)

   💡 Razones:
   - [Razón 1: ej. "Promedio de 25.4 pts en últimos 5 juegos"]
   - [Razón 2: ej. "Consistencia alta (CV: 12%)"]
   - [Razón 3: ej. "Juega en casa vs defensa débil (DAL #28)"]
   - [Razón 4: ej. "Tendencia ascendente: 22, 24, 26, 28, 30 pts"]

─────────────────────────────────────────────────────────────

📊 REBOTES (REB)
   Promedio últimos 5: [μ] reb
   Desviación estándar: [σ] reb
   Rango típico: [[μ-σ], [μ+σ]] reb
   Consistencia: [CV]% - [MUY/MODERADAMENTE/IN]CONSISTENTE

   🎯 LÍNEA RECOMENDADA: [X.5] rebotes

   📈 RECOMENDACIÓN: OVER / UNDER
   🔥 Confianza: ⭐⭐⭐⭐ (1-5 estrellas)

   💡 Razones:
   - [Razón 1]
   - [Razón 2]
   - [Razón 3]

─────────────────────────────────────────────────────────────

📊 ASISTENCIAS (AST)
   Promedio últimos 5: [μ] ast
   Desviación estándar: [σ] ast
   Rango típico: [[μ-σ], [μ+σ]] ast
   Consistencia: [CV]% - [MUY/MODERADAMENTE/IN]CONSISTENTE

   🎯 LÍNEA RECOMENDADA: [X.5] asistencias

   📈 RECOMENDACIÓN: OVER / UNDER
   🔥 Confianza: ⭐⭐⭐⭐ (1-5 estrellas)

   💡 Razones:
   - [Razón 1]
   - [Razón 2]
   - [Razón 3]

═════════════════════════════════════════════════════════════

📋 RESUMEN DE APUESTAS RECOMENDADAS:
   ✅ OVER Puntos [X.5] - Confianza: ⭐⭐⭐⭐⭐
   ✅ UNDER Rebotes [X.5] - Confianza: ⭐⭐⭐
   ⚠️  SKIP Asistencias (Baja confianza)

═════════════════════════════════════════════════════════════
```

---

### 4. NIVELES DE CONFIANZA

**⭐⭐⭐⭐⭐ MUY ALTA (5 estrellas)**:
- CV < 15% (muy consistente)
- Tendencia clara y sostenida
- Contexto favorable (casa, oponente débil)
- Mínimo 4 de 5 juegos en el rango esperado

**⭐⭐⭐⭐ ALTA (4 estrellas)**:
- CV 15-20%
- Tendencia moderada
- Contexto neutral o ligeramente favorable
- 3 de 5 juegos en el rango esperado

**⭐⭐⭐ MEDIA (3 estrellas)**:
- CV 20-25%
- Sin tendencia clara
- Contexto neutral
- 3 de 5 juegos en el rango esperado

**⭐⭐ BAJA (2 estrellas)**:
- CV 25-30%
- Tendencia inconsistente
- Contexto desfavorable
- Menos de 3 de 5 juegos en el rango

**⭐ MUY BAJA (1 estrella)**:
- CV > 30%
- Altamente inconsistente
- Datos insuficientes o conflictivos
- **RECOMENDACIÓN: SKIP (No apostar)**

---

### 5. COMPARACIÓN CON CASAS DE APUESTAS

Si se dispone de líneas de casas de apuestas (DraftKings, FanDuel, BetMGM, etc.), comparar:

```
🏦 LÍNEAS DE CASAS DE APUESTAS vs MODELO

Jugador: [Nombre]
Métrica: PUNTOS

┌─────────────────┬──────────┬──────────┬──────────┐
│ Casa de Apuestas│  Línea   │   Over   │  Under   │
├─────────────────┼──────────┼──────────┼──────────┤
│ DraftKings      │   24.5   │  -110    │  -110    │
│ FanDuel         │   25.0   │  -115    │  -105    │
│ BetMGM          │   24.5   │  -105    │  -115    │
│ Caesars         │   25.0   │  -110    │  -110    │
└─────────────────┴──────────┴──────────┴──────────┘

📊 MODELO PROPIO: 26.5 puntos → OVER 25.0

💰 VALUE BET DETECTADO:
   OVER 24.5 en DraftKings (-110)
   OVER 25.0 en FanDuel (-115)

🎯 EDGE ESTIMADO: +2 puntos sobre línea del mercado
🔥 RECOMENDACIÓN: STRONG BET en OVER

⚠️  NOTA: Si todas las casas coinciden en una línea y difiere
    significativamente del modelo, revisar si hay información
    no capturada (lesión, cambio de rotación, etc.)
```

---

### 6. ANÁLISIS DE MÚLTIPLES JUGADORES

Para análisis completo de todos los partidos del día:

1. **Ordenar por Confianza**: Listar primero las apuestas de 5 estrellas
2. **Agrupar por Partido**: Facilitar análisis de parlays
3. **Identificar Correlaciones**: ej. "Si Curry Over PTS, es probable Over 3PM"
4. **Resumen Ejecutivo**: Top 10 apuestas del día

#### Formato de Resumen:

```
═══════════════════════════════════════════════════════════════
🏆 TOP 10 APUESTAS DEL DÍA - [FECHA]
═══════════════════════════════════════════════════════════════

1. ⭐⭐⭐⭐⭐ Luka Doncic OVER 32.5 PTS (DAL vs HOU)
   → Promedio: 35.2 | CV: 11% | Línea del mercado: 31.5

2. ⭐⭐⭐⭐⭐ Anthony Davis OVER 12.5 REB (LAL vs SAS)
   → Promedio: 13.8 | CV: 13% | Línea del mercado: 12.0

3. ⭐⭐⭐⭐⭐ Tyrese Haliburton OVER 9.5 AST (IND vs CHA)
   → Promedio: 11.4 | CV: 14% | Línea del mercado: 9.5

[... continuar con las demás ...]

═══════════════════════════════════════════════════════════════
```

---

## INSTRUCCIONES ESPECÍFICAS DE USO

### Para Análisis Manual:
1. Leer CSV generado por scraper (`[TEAM]_last_5_games_ALL_QUARTERS.csv`)
2. Aplicar cálculos estadísticos mencionados
3. Evaluar contexto del partido de hoy
4. Generar recomendaciones con formato especificado

### Para Análisis Automatizado con IA:
1. Pasar este prompt completo junto con los datos CSV
2. Solicitar análisis siguiendo la metodología exacta
3. Validar que incluya:
   - ✅ Cálculos estadísticos (μ, σ, CV)
   - ✅ Análisis de tendencias
   - ✅ Contexto del partido
   - ✅ Líneas recomendadas
   - ✅ Niveles de confianza
   - ✅ Razones detalladas

---

## NOTAS IMPORTANTES

⚠️ **DISCLAIMER**: Este análisis es una herramienta de apoyo estadístico. Las apuestas deportivas conllevan riesgo financiero. Siempre:
- Verificar líneas oficiales de casas de apuestas
- Considerar noticias de última hora (lesiones, descansos)
- Apostar responsablemente
- No apostar más de lo que puedas perder

🔄 **ACTUALIZACIÓN**: Los datos deben ser actualizados diariamente antes de cada sesión de apuestas para reflejar los juegos más recientes.

📊 **VALIDACIÓN**: Se recomienda trackear las recomendaciones y calcular el ROI (Return on Investment) para ajustar el modelo con el tiempo.

---

## EJEMPLO COMPLETO DE ANÁLISIS

```
🏀 JUGADOR: Nikola Jokic (DEN)
📅 Partido de HOY: DEN vs LAL | Casa | 7:00 PM ET

─────────────────────────────────────────────────────────────

📊 PUNTOS (PTS)
   Promedio últimos 5: 28.6 pts
   Desviación estándar: 3.2 pts
   Rango típico: [25.4, 31.8] pts
   Consistencia: 11.2% - MUY CONSISTENTE ✅

   Distribución últimos 5 juegos: 26, 28, 31, 27, 31 pts

   🎯 LÍNEA RECOMENDADA: 28.5 puntos

   📈 RECOMENDACIÓN: OVER 28.5
   🔥 Confianza: ⭐⭐⭐⭐⭐

   💡 Razones:
   - Promedio de 28.6 pts superando ligeramente la línea
   - Consistencia excepcional (CV: 11.2%)
   - 4 de 5 últimos juegos con 27+ puntos
   - Juega en casa donde promedia 30.2 pts esta temporada
   - LAL permite 115.3 pts/juego (defensa #22 de la liga)
   - Sin minutos limitados (promedio 35.4 min últimos 5)

─────────────────────────────────────────────────────────────

📊 REBOTES (REB)
   Promedio últimos 5: 13.2 reb
   Desviación estándar: 2.1 reb
   Rango típico: [11.1, 15.3] reb
   Consistencia: 15.9% - MODERADAMENTE CONSISTENTE ⚠️

   Distribución últimos 5 juegos: 11, 15, 14, 12, 14 reb

   🎯 LÍNEA RECOMENDADA: 12.5 rebotes

   📈 RECOMENDACIÓN: OVER 12.5
   🔥 Confianza: ⭐⭐⭐⭐

   💡 Razones:
   - Promedio de 13.2 reb bien sobre la línea
   - 4 de 5 juegos con 12+ rebotes
   - LAL sin Anthony Davis (lesionado) - más rebotes disponibles
   - Jokic lidera equipo en rebotes (sin competencia interna)

─────────────────────────────────────────────────────────────

📊 ASISTENCIAS (AST)
   Promedio últimos 5: 11.4 ast
   Desviación estándar: 2.8 ast
   Rango típico: [8.6, 14.2] ast
   Consistencia: 24.6% - MODERADAMENTE CONSISTENTE ⚠️

   Distribución últimos 5 juegos: 9, 14, 12, 8, 14 ast

   🎯 LÍNEA RECOMENDADA: 10.5 asistencias

   📈 RECOMENDACIÓN: OVER 10.5
   🔥 Confianza: ⭐⭐⭐

   💡 Razones:
   - Promedio de 11.4 ast sobre la línea
   - Variabilidad moderada (CV: 24.6%)
   - 3 de 5 juegos con 11+ asistencias
   - Jamal Murray de vuelta (más opciones de pase)
   - ⚠️ Confianza media por inconsistencia

═════════════════════════════════════════════════════════════

📋 RESUMEN DE APUESTAS RECOMENDADAS:
   ✅ OVER Puntos 28.5 - Confianza: ⭐⭐⭐⭐⭐
   ✅ OVER Rebotes 12.5 - Confianza: ⭐⭐⭐⭐
   ✅ OVER Asistencias 10.5 - Confianza: ⭐⭐⭐

💰 PARLAY SUGERIDO:
   Jokic Triple OVER (28.5 PTS / 12.5 REB / 10.5 AST)
   Riesgo: Medio | Potencial: Alto

═════════════════════════════════════════════════════════════
```

---

## FIN DEL PROMPT
