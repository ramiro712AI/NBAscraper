# 🏀 NBA Betting Analyzer - Sistema Completo de Análisis de Apuestas

Sistema completo y automatizado para analizar estadísticas de jugadores NBA y generar recomendaciones precisas de **OVER/UNDER** en puntos, rebotes y asistencias, comparando con líneas de casas de apuestas.

---

## 📋 TABLA DE CONTENIDOS

1. [Características](#características)
2. [Instalación](#instalación)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Flujo de Trabajo](#flujo-de-trabajo)
5. [Uso del Sistema](#uso-del-sistema)
6. [Configuración de APIs](#configuración-de-apis)
7. [Interpretación de Resultados](#interpretación-de-resultados)
8. [Ejemplos](#ejemplos)
9. [FAQ](#faq)

---

## ✨ CARACTERÍSTICAS

### 🔍 Scraping Automatizado
- ✅ Detección automática de juegos del día
- ✅ Extracción de estadísticas de últimos 5 juegos
- ✅ Desglose por quarters (Q1, Q2, Q3, Q4)
- ✅ Métricas: PTS, REB, AST, 3PM

### 📊 Análisis Estadístico Avanzado
- ✅ Cálculo de promedios, desviación estándar y coeficiente de variación
- ✅ Análisis de tendencias (ascendente, descendente, estable)
- ✅ Evaluación de consistencia del jugador
- ✅ Contexto de partido (casa/visitante, oponente)

### 🎯 Generación de Líneas Over/Under
- ✅ Líneas personalizadas basadas en datos históricos
- ✅ Niveles de confianza (1-5 estrellas)
- ✅ Recomendaciones OVER/UNDER con razones detalladas
- ✅ Resumen ejecutivo de mejores apuestas

### 💰 Integración con Casas de Apuestas
- ✅ Comparación con líneas del mercado
- ✅ Detección automática de VALUE BETS
- ✅ Soporte para múltiples sportsbooks (DraftKings, FanDuel, BetMGM, etc.)
- ✅ Modo mock para testing sin API key

---

## 🚀 INSTALACIÓN

### Requisitos
- Python 3.7+
- Pandas
- NumPy
- Requests

### Instalación de Dependencias

```bash
pip install pandas numpy requests
```

---

## 📁 ESTRUCTURA DEL PROYECTO

```
NBAscraper/
│
├── 📄 nba_nuevo.py                    # Scraper mejorado (extrae Q1-Q4 + totales)
├── 📄 nba_auto_scraper.py             # Scraper automático para juegos del día
│
├── 📄 betting_analyzer.py             # ⭐ Analizador principal de apuestas
├── 📄 sportsbook_integration.py       # 💰 Integración con casas de apuestas
│
├── 📄 betting_analysis_prompt.md      # 📖 Prompt completo para análisis manual/IA
├── 📄 sportsbook_config.json          # ⚙️ Configuración de APIs de casas
│
├── 📄 run_nba_scraper.bat             # Script de ejecución (Windows)
└── 📄 README_BETTING.md               # Este archivo
```

---

## 🔄 FLUJO DE TRABAJO

### Proceso Completo (3 Pasos)

```
┌─────────────────────────────────────────────────────────────┐
│  PASO 1: SCRAPING DE DATOS                                  │
│  ──────────────────────────────────────────────────────────│
│  python nba_nuevo.py                                        │
│                                                             │
│  → Detecta equipos que juegan HOY                          │
│  → Extrae últimos 5 juegos de cada equipo                 │
│  → Genera CSVs: [TEAM]_last_5_games_ALL_QUARTERS.csv      │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  PASO 2: ANÁLISIS Y RECOMENDACIONES                        │
│  ──────────────────────────────────────────────────────────│
│  python betting_analyzer.py                                 │
│                                                             │
│  → Lee todos los CSVs generados                            │
│  → Calcula métricas estadísticas (μ, σ, CV)               │
│  → Genera líneas de over/under                             │
│  → Asigna niveles de confianza                             │
│  → Crea reporte completo: betting_report_[TIMESTAMP].txt  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  PASO 3: COMPARACIÓN CON MERCADO (Opcional)               │
│  ──────────────────────────────────────────────────────────│
│  python sportsbook_integration.py                           │
│                                                             │
│  → Obtiene líneas de casas de apuestas                     │
│  → Compara con líneas del modelo                           │
│  → Detecta VALUE BETS (edge positivo)                      │
│  → Genera reporte de oportunidades                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎮 USO DEL SISTEMA

### 1️⃣ Obtener Datos de Jugadores

**Opción A: Scraper Automático (Recomendado)**

```bash
python nba_nuevo.py
```

**Qué hace:**
- Detecta automáticamente qué equipos juegan HOY
- Descarga estadísticas de últimos 5 juegos de cada equipo
- Genera CSVs con desglose completo por quarters

**Salida:**
```
LAL_last_5_games_ALL_QUARTERS.csv
BOS_last_5_games_ALL_QUARTERS.csv
GSW_last_5_games_ALL_QUARTERS.csv
...
```

---

### 2️⃣ Generar Análisis de Apuestas

```bash
python betting_analyzer.py
```

**Qué hace:**
- Lee todos los CSVs encontrados en el directorio
- Analiza cada jugador individualmente
- Calcula:
  - Promedio de últimos 5 juegos
  - Desviación estándar
  - Coeficiente de variación (consistencia)
  - Tendencia reciente
- Genera líneas de over/under
- Asigna nivel de confianza (1-5 estrellas)
- Crea reporte detallado

**Salida:**
```
betting_report_20231202_143045.txt
```

**Reporte incluye:**
- ✅ Análisis individual de cada jugador (PTS, REB, AST)
- ✅ Líneas recomendadas con nivel de confianza
- ✅ Razones detalladas para cada recomendación
- ✅ Top 10 mejores apuestas del día
- ✅ Sugerencias de parlays

---

### 3️⃣ Comparar con Casas de Apuestas

```bash
python sportsbook_integration.py
```

**Qué hace:**
- Obtiene líneas actuales de casas de apuestas
- Compara con líneas del modelo
- Identifica discrepancias (VALUE BETS)
- Calcula el "edge" (ventaja) del modelo

**Modo Mock (Sin API Key):**
- Genera datos de ejemplo para testing
- Útil para aprender el sistema

**Modo Real (Con API Key):**
- Conecta a The Odds API u otros servicios
- Obtiene líneas reales del mercado
- Detecta oportunidades reales de value betting

---

## ⚙️ CONFIGURACIÓN DE APIs

### The Odds API (Recomendado)

**Por qué The Odds API:**
- ✅ 500 requests gratis por mes
- ✅ Agrega odds de múltiples casas (DraftKings, FanDuel, etc.)
- ✅ API simple y bien documentada
- ✅ Soporte para player props

**Cómo Configurar:**

1. **Registrarse en The Odds API**
   ```
   https://the-odds-api.com/
   ```

2. **Obtener API Key**
   - Crear cuenta (gratis)
   - Copiar tu API key del dashboard

3. **Actualizar configuración**
   Editar `sportsbook_config.json`:
   ```json
   {
     "sportsbooks": {
       "odds_api": {
         "api_key": "TU_API_KEY_AQUI"
       }
     }
   }
   ```

4. **Ejecutar**
   ```bash
   python sportsbook_integration.py
   ```

### Otras APIs Soportadas

- **DraftKings API** (Partners verificados)
- **FanDuel API** (Partners verificados)
- **BetMGM API** (Partners verificados)

**Nota:** APIs de casas individuales requieren aprobación como partner.

---

## 📊 INTERPRETACIÓN DE RESULTADOS

### Niveles de Confianza

| Estrellas | CV        | Interpretación                              | Acción Recomendada |
|-----------|-----------|---------------------------------------------|--------------------|
| ⭐⭐⭐⭐⭐  | < 15%     | MUY CONSISTENTE - Alta confianza           | ✅ Apuesta fuerte   |
| ⭐⭐⭐⭐    | 15-20%    | CONSISTENTE - Buena confianza              | ✅ Apostar          |
| ⭐⭐⭐      | 20-25%    | MODERADO - Confianza media                 | ⚠️ Apostar con cautela |
| ⭐⭐        | 25-30%    | INCONSISTENTE - Baja confianza             | ❌ Evitar           |
| ⭐         | > 30%     | MUY INCONSISTENTE - Muy baja confianza     | ❌ SKIP             |

### Coeficiente de Variación (CV)

**¿Qué es?**
- Mide la variabilidad relativa de los datos
- CV = (Desviación Estándar / Promedio) × 100%

**Interpretación:**
- **CV < 15%**: El jugador es muy predecible ✅
- **CV 15-25%**: Variabilidad normal ⚠️
- **CV > 25%**: Rendimiento errático ❌

**Ejemplo:**
```
Jugador A: μ=25 pts, σ=2 pts → CV=8% (MUY CONSISTENTE)
Jugador B: μ=25 pts, σ=8 pts → CV=32% (INCONSISTENTE)
```

### Tendencias

- **📈 UP (Ascendente)**: Últimos juegos muestran mejora → Favorece OVER
- **📉 DOWN (Descendente)**: Últimos juegos muestran declive → Favorece UNDER
- **➡️ STABLE (Estable)**: Sin cambios significativos → Usar promedio

### Value Bets

**¿Qué es un Value Bet?**
- Cuando tu línea proyectada difiere significativamente de la línea del mercado
- Indica una posible ventaja estadística

**Ejemplo:**
```
Tu modelo: OVER 28.5 puntos
DraftKings: Línea 25.5 puntos
Edge: +3 puntos → STRONG VALUE BET! 💰
```

**Criterio de Value:**
- Edge > 1.5 puntos: Value moderado
- Edge > 2.5 puntos: Strong value
- Edge > 4 puntos: Revisar (posible información no capturada)

---

## 📋 EJEMPLOS

### Ejemplo 1: Reporte de Jugador

```
═════════════════════════════════════════════════════════════
🏀 JUGADOR: Nikola Jokic (DEN)
═════════════════════════════════════════════════════════════

─────────────────────────────────────────────────────────────

📊 PUNTOS (PTS)
   Promedio últimos 5: 28.6 pts
   Desviación estándar: 3.2 pts
   Rango típico: [25.4, 31.8] pts
   Consistencia: 11.2% - MUY CONSISTENTE ✅

   Distribución últimos 5 juegos: 26, 28, 31, 27, 31 pts

   🎯 LÍNEA RECOMENDADA: 28.5 puntos

   📈 RECOMENDACIÓN: OVER 28.5
   🔥 Confianza: ⭐⭐⭐⭐⭐ (MUY ALTA)

   💡 Razones:
   - Promedio de 28.6 pts superando ligeramente la línea
   - Consistencia excepcional (CV: 11.2%)
   - 4 de 5 últimos juegos con 27+ puntos
   - Rango típico: [25.4, 31.8] pts

─────────────────────────────────────────────────────────────

📋 RESUMEN DE APUESTAS RECOMENDADAS:
   ✅ OVER Puntos 28.5 - Confianza: ⭐⭐⭐⭐⭐
   ✅ OVER Rebotes 12.5 - Confianza: ⭐⭐⭐⭐
   ✅ OVER Asistencias 10.5 - Confianza: ⭐⭐⭐

💰 PARLAY SUGERIDO:
   OVER 28.5 PTS / OVER 12.5 REB / OVER 10.5 AST
   Riesgo: Bajo | Potencial: Alto

═════════════════════════════════════════════════════════════
```

### Ejemplo 2: Top Apuestas del Día

```
═════════════════════════════════════════════════════════════
🏆 TOP 10 APUESTAS DEL DÍA - 2023-12-02
═════════════════════════════════════════════════════════════

1. ⭐⭐⭐⭐⭐ Luka Doncic OVER 32.5 PTS (DAL)
   → Promedio: 35.2 | CV: 11%

2. ⭐⭐⭐⭐⭐ Anthony Davis OVER 12.5 REB (LAL)
   → Promedio: 13.8 | CV: 13%

3. ⭐⭐⭐⭐⭐ Tyrese Haliburton OVER 9.5 AST (IND)
   → Promedio: 11.4 | CV: 14%

4. ⭐⭐⭐⭐⭐ Giannis Antetokounmpo OVER 30.5 PTS (MIL)
   → Promedio: 32.8 | CV: 12%

...

═════════════════════════════════════════════════════════════
```

### Ejemplo 3: Value Bet Detectado

```
═══════════════════════════════════════════════════════════════
💎 VALUE BETS DETECTADOS - 2023-12-02
═══════════════════════════════════════════════════════════════

1. ⭐⭐⭐⭐⭐
   🏀 Luka Doncic - PTS
   📊 OVER 31.5
   🏦 DraftKings (-110)
   💰 Edge: +3.7 vs modelo

2. ⭐⭐⭐⭐
   🏀 Anthony Davis - REB
   📊 OVER 11.5
   🏦 FanDuel (-105)
   💰 Edge: +2.3 vs modelo

═══════════════════════════════════════════════════════════════
```

---

## ❓ FAQ

### ¿Con qué frecuencia debo ejecutar el scraper?
**Una vez al día**, antes de los juegos. Lo ideal es ejecutarlo 2-3 horas antes del primer juego del día.

### ¿Cuántos juegos históricos analiza?
**5 juegos más recientes** de cada jugador. Es un balance entre datos suficientes y relevancia temporal.

### ¿Puedo cambiar el número de juegos analizados?
Sí, en `nba_nuevo.py` modifica el parámetro `limit=5` en la función `get_team_schedule()`.

### ¿El sistema considera lesiones o descansos?
No automáticamente. Debes verificar manualmente el injury report antes de apostar.

### ¿Funciona en Mac/Linux?
Sí, solo `run_nba_scraper.bat` es específico de Windows. Puedes ejecutar directamente:
```bash
python nba_nuevo.py && python betting_analyzer.py
```

### ¿Es legal usar este sistema para apuestas?
Sí, el análisis estadístico es completamente legal. Sin embargo:
- ✅ Verifica que las apuestas deportivas sean legales en tu jurisdicción
- ✅ Apuesta responsablemente
- ✅ Nunca apuestes más de lo que puedes perder

### ¿Garantiza ganancias?
**NO.** Este es un sistema de apoyo estadístico. Las apuestas deportivas siempre conllevan riesgo. Usar con responsabilidad.

### ¿Cómo trackeo mi ROI?
Recomendamos:
1. Llevar un registro de todas las apuestas
2. Anotar línea, stake, resultado
3. Calcular ROI mensual: `(Ganancias - Pérdidas) / Total Apostado × 100%`

### ¿Puedo usar esto para otros deportes?
Sí, la metodología es adaptable. Ya incluye `nhl_scraper.py` para hockey. Puedes crear scrapers para NFL, MLB, etc.

---

## ⚠️ DISCLAIMER

**IMPORTANTE:**
- Este sistema es una **herramienta de apoyo estadístico**
- No garantiza ganancias
- Las apuestas deportivas conllevan riesgo financiero
- Siempre verifica información de última hora (lesiones, descansos)
- Apuesta responsablemente
- No apuestes más de lo que puedas perder

**RESPONSABILIDAD:**
- Los desarrolladores no se hacen responsables de pérdidas financieras
- Uso bajo tu propio riesgo
- Conoce las leyes de apuestas de tu jurisdicción

---

## 📞 SOPORTE

Para preguntas, reportar bugs o sugerir mejoras:
- 📧 Email: [tu-email@example.com]
- 🐛 Issues: [GitHub Issues]

---

## 📝 LICENCIA

[MIT License o la que prefieras]

---

## 🙏 CRÉDITOS

- **Datos:** ESPN API
- **Odds:** The Odds API
- **Librerías:** Pandas, NumPy, Requests

---

## 🔄 ACTUALIZACIONES

**v1.0.0** (2023-12-02)
- ✅ Sistema completo de análisis de apuestas
- ✅ Scraper automático con desglose por quarters
- ✅ Generación de líneas over/under
- ✅ Integración con casas de apuestas
- ✅ Detección de value bets
- ✅ Reportes detallados con niveles de confianza

---

**¡BUENA SUERTE Y APUESTA RESPONSABLEMENTE! 🍀**
