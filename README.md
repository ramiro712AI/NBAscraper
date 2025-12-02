# 🏀 NBA Betting Analyzer - Sistema Completo

Sistema automatizado para análisis de apuestas NBA con generación de líneas Over/Under y detección de value bets.

## 🚀 USO RÁPIDO

### Ejecutar Todo el Sistema (1 Comando)

**En Windows:**
```bash
run_betting_complete.bat
```

**En Mac/Linux:**
```bash
python nba_betting_complete.py
```

Esto ejecuta automáticamente:
1. ✅ Scraping de juegos del día
2. ✅ Análisis estadístico completo
3. ✅ Comparación con casas de apuestas
4. ✅ Generación de reportes

---

## 📋 ¿QUÉ HACE EL SISTEMA?

### 🔍 Paso 1: Scraping Automático
- Detecta qué equipos juegan HOY
- Descarga estadísticas de últimos 5 juegos
- Genera CSVs con desglose por quarters (Q1-Q4)

### 📊 Paso 2: Análisis Estadístico
- Calcula promedios, desviación estándar y coeficiente de variación
- Genera líneas de Over/Under personalizadas
- Asigna niveles de confianza (⭐⭐⭐⭐⭐)
- Identifica tendencias y consistencia

### 💰 Paso 3: Comparación con Mercado
- Obtiene líneas de DraftKings, FanDuel, BetMGM, etc.
- Compara con líneas del modelo
- Detecta VALUE BETS automáticamente
- Calcula el "edge" sobre el mercado

---

## 📊 SALIDA DEL SISTEMA

### Archivos Generados:

```
📁 CSVs de Datos:
   LAL_last_5_games_ALL_QUARTERS.csv
   BOS_last_5_games_ALL_QUARTERS.csv
   ...

📄 Reportes:
   betting_report_20231202_143045.txt    ← Análisis completo
   value_bets_20231202_143045.txt        ← Oportunidades de value
```

### Ejemplo de Reporte:

```
═══════════════════════════════════════════════════════════════
🏀 JUGADOR: Nikola Jokic (DEN)
═══════════════════════════════════════════════════════════════

📊 PUNTOS (PTS)
   Promedio últimos 5: 28.6 pts
   Consistencia: 11.2% - MUY CONSISTENTE ✅

   🎯 LÍNEA RECOMENDADA: 28.5 puntos
   📈 RECOMENDACIÓN: OVER 28.5
   🔥 Confianza: ⭐⭐⭐⭐⭐

───────────────────────────────────────────────────────────────

💎 VALUE BETS DETECTADOS:

1. ⭐⭐⭐⭐⭐
   🏀 Luka Doncic - PTS
   📊 OVER 31.5
   🏦 DraftKings (-110)
   💰 Edge: +3.7 vs modelo
```

---

## ⚙️ INSTALACIÓN

### Requisitos:
```bash
pip install pandas numpy requests
```

### Configuración de API (Opcional):
- El sistema funciona con datos mock por defecto
- Para odds reales: API key ya configurada en `sportsbook_config.json`
- The Odds API: 500 requests gratis/mes

---

## 📖 DOCUMENTACIÓN COMPLETA

Para guía detallada, ver: **[README_BETTING.md](README_BETTING.md)**

Incluye:
- Interpretación de métricas
- Niveles de confianza
- Ejemplos completos
- FAQ y troubleshooting

---

## 📁 ESTRUCTURA DEL PROYECTO

```
NBAscraper/
├── nba_betting_complete.py       ⭐ SCRIPT PRINCIPAL
├── run_betting_complete.bat      ⭐ Ejecutable Windows
│
├── nba_nuevo.py                   Scraper de datos
├── betting_analyzer.py            Analizador estadístico
├── sportsbook_integration.py      Integración con APIs
│
├── betting_analysis_prompt.md     Metodología completa
├── sportsbook_config.json         Configuración de APIs
└── README_BETTING.md              Documentación completa
```

---

## 🎯 USO AVANZADO

### Ejecutar Pasos Individuales:

```bash
# Solo scraping
python nba_nuevo.py

# Solo análisis (requiere CSVs previos)
python betting_analyzer.py

# Solo comparación con mercado
python sportsbook_integration.py
```

---

## 📊 INTERPRETACIÓN DE RESULTADOS

### Niveles de Confianza:

| Estrellas | Consistencia | Acción |
|-----------|-------------|---------|
| ⭐⭐⭐⭐⭐ | MUY ALTA (CV < 15%) | ✅ Apuesta fuerte |
| ⭐⭐⭐⭐ | ALTA (CV 15-20%) | ✅ Apostar |
| ⭐⭐⭐ | MEDIA (CV 20-25%) | ⚠️ Cautela |
| ⭐⭐ | BAJA (CV 25-30%) | ❌ Evitar |
| ⭐ | MUY BAJA (CV > 30%) | ❌ SKIP |

### Value Bets:
- **Edge > 1.5 pts**: Value moderado
- **Edge > 2.5 pts**: Strong value 💰
- **Edge > 4 pts**: Revisar información adicional

---

## ⚠️ DISCLAIMER

Este sistema es una **herramienta de apoyo estadístico**.

- ✅ No garantiza ganancias
- ✅ Siempre verifica injury reports
- ✅ Apuesta responsablemente
- ✅ No apuestes más de lo que puedas perder

---

## 💡 RECOMENDACIONES

1. **Ejecuta diariamente** 2-3 horas antes de los juegos
2. **Verifica lesiones** en NBA.com o ESPN
3. **Trackea tus apuestas** para calcular ROI
4. **Combina con tu análisis** - no sigas ciegamente
5. **Gestiona tu bankroll** - nunca apuestes todo en un día

---

## 🔄 FRECUENCIA DE USO

```
Diario:
- Ejecutar nba_betting_complete.py cada día que haya juegos
- Comparar líneas 2-3 horas antes del primer juego
- Actualizar análisis si hay noticias de última hora

Semanal:
- Revisar ROI de las apuestas recomendadas
- Ajustar umbrales de confianza si es necesario

Mensual:
- Analizar rendimiento general del sistema
- Documentar patrones y mejoras
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### "No hay juegos programados para HOY"
- Es normal si no hay juegos NBA ese día
- Verifica en ESPN.com/nba

### "Error obteniendo odds"
- Verifica conexión a internet
- Revisa API key en `sportsbook_config.json`
- Modo mock se activará automáticamente

### "No se encontraron archivos CSV"
- Ejecuta primero `python nba_nuevo.py`
- O usa el script completo: `python nba_betting_complete.py`

---

## 📞 SOPORTE

Para preguntas o mejoras, contacta al desarrollador o abre un issue.

---

## 📝 VERSIÓN

**v2.0.0** - Sistema Unificado
- ✅ Script único para todo el proceso
- ✅ Análisis estadístico avanzado
- ✅ Integración con casas de apuestas
- ✅ Detección automática de value bets
- ✅ Reportes detallados con niveles de confianza

---

**¡BUENA SUERTE Y APUESTA RESPONSABLEMENTE! 🍀**
