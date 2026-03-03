# Day Trading Bot — Señales en Tiempo Real

Sistema completo de señales de trading para **acciones** y **criptomonedas**.

---

## Archivos

| Archivo | Descripción |
|---|---|
| `trading_signals.py` | Motor de indicadores técnicos + generador de señales |
| `trading_dashboard.py` | Gráficos interactivos (Plotly) con señales BUY/SELL |
| `trading_bot.py` | Bot automatizado con gestión de posiciones (paper trading) |
| `requirements_trading.txt` | Dependencias Python |

---

## Instalación rápida

```bash
pip install -r requirements_trading.txt
```

---

## Uso

### 1. Escanear señales (terminal)
```bash
python trading_signals.py
```
Muestra señales BUY/SELL/HOLD para stocks y crypto con Stop-Loss y Take-Profit.

### 2. Gráfico interactivo en el navegador
```bash
# Gráfico de BTC-USD (default)
python trading_dashboard.py

# Gráfico de TSLA con velas de 5 minutos
python trading_dashboard.py TSLA 5d 5m

# Gráfico de ETH-USD con velas de 1 hora
python trading_dashboard.py ETH-USD 1mo 1h
```

### 3. Bot automático (paper trading)
```bash
# Escanear una sola vez
python trading_bot.py --once

# Loop cada 15 minutos (corre indefinidamente)
python trading_bot.py

# Loop cada 5 minutos
python trading_bot.py --interval 5
```

---

## Indicadores técnicos usados

| Indicador | Parámetros | Uso |
|---|---|---|
| **RSI** | período 14 | <30 = oversold (BUY), >70 = overbought (SELL) |
| **MACD** | 12/26/9 | Cruce del histograma = cambio de tendencia |
| **Bollinger Bands** | 20/2σ | Precio bajo banda = BUY, sobre banda = SELL |
| **EMA** | 9/21/50 | Cruce 9>21 = bullish, precio>EMA50 = tendencia alcista |
| **ATR** | período 14 | Calcula Stop-Loss (1.5×ATR) y Take-Profit (3×ATR) |
| **Volume** | MA20 | Confirma la señal cuando volumen > 1.5× promedio |

---

## Sistema de puntuación

Cada indicador aporta puntos positivos (BUY) o negativos (SELL):

```
RSI         → ±20 pts
MACD flip   → ±25 pts
Bollinger   → ±20 pts
EMA cross   → ±25 pts
Volumen     → ±10 pts
─────────────────────
Score ≥  60 → BUY
Score ≤ -60 → SELL
Otro        → HOLD
```

---

## Gestión de riesgo

- **Stop-Loss**: entrada − 1.5 × ATR
- **Take-Profit**: entrada + 3.0 × ATR (ratio riesgo:recompensa = 1:2)
- Capital fijo por operación (configurable en `BotConfig`)
- Máximo de posiciones abiertas simultáneas

---

## Alertas (opcional)

Edita la función `notify()` en `trading_bot.py` para enviar alertas a:
- **Telegram** (recomendado para móvil)
- **Discord** webhook
- **Email** con smtplib

---

## Intervalos de datos soportados

| Intervalo | Período máximo | Uso recomendado |
|---|---|---|
| `1m` | 7 días | Scalping |
| `5m` | 60 días | Day trading rápido |
| `15m` | 60 días | Day trading estándar |
| `1h` | 730 días | Swing trading |
| `1d` | max | Inversión largo plazo |

---

## Disclaimer

> Este software es solo para **fines educativos y paper trading**.
> No constituye asesoría financiera. Opera siempre con capital que
> puedas permitirte perder. Backtest tu estrategia antes de usar
> dinero real.
