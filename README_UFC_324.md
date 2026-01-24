# UFC 324 Fighter Analysis Script

Script de Python para extraer y analizar las últimas 5 peleas de cada peleador del UFC 324 (24 de enero de 2026).

## Descripción

Este script analiza los 26 peleadores programados para UFC 324, extrayendo información detallada de sus últimas 5 peleas y generando estadísticas completas.

### Evento: UFC 324
- **Fecha:** 24 de Enero 2026
- **Total Peleadores:** 26 (13 peleas, 1 cancelada)

## Instalación

### Requisitos del Sistema
- Python 3.8 o superior
- Conexión a internet (para web scraping)

### Dependencias

```bash
pip install -r requirements_ufc.txt
```

O instalar manualmente:

```bash
pip install requests beautifulsoup4 pandas openpyxl lxml
```

## Uso

### Ejecución Básica (con datos demo)

```bash
python ufc_fighter_analysis.py
```

### Ejecución con Web Scraping Real

```bash
python ufc_fighter_analysis.py --scrape
```

### Especificar Directorio de Salida

```bash
python ufc_fighter_analysis.py --output ./reportes
```

### Todas las Opciones

```bash
python ufc_fighter_analysis.py --scrape --output ./reportes
```

## Datos Extraídos por Peleador

Para cada una de las últimas 5 peleas se extrae:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| Fecha | Fecha de la pelea | "Nov 16, 2024" |
| Oponente | Nombre del oponente | "Max Holloway" |
| Resultado | Win/Loss/Draw/NC | "Win" |
| Método | Tipo de finalización | "KO", "TKO", "Submission", "Decision" |
| Detalle del Método | Técnica específica | "Rear Naked Choke", "Unanimous", "Punches" |
| Round | Round en que terminó | 2 |
| Tiempo | Tiempo exacto (mm:ss) | "3:22" |
| Evento | Evento UFC | "UFC 310" |

### Métodos de Victoria/Derrota Soportados

- **KO/TKO:** Con especificación de strikes (punches, kicks, elbows, etc.)
- **Submission:** Con técnica exacta (RNC, Armbar, Guillotine, Triangle, Kimura, etc.)
- **Decision:** Unanimous, Split, Majority
- **DQ:** Descalificación
- **NC:** No Contest

## Estadísticas Generadas

Para cada peleador se calculan:

| Estadística | Descripción |
|-------------|-------------|
| Win Rate (%) | Porcentaje de victorias en últimas 5 peleas |
| Método Más Frecuente | Método de victoria más común |
| Promedio de Rounds | Media de rounds por pelea |
| Racha Actual | Secuencia de resultados (ej: 3W significa 3 victorias consecutivas) |
| Finish Rate (%) | Porcentaje de victorias por finalización |
| Decision Rate (%) | Porcentaje de victorias por decisión |

## Archivos de Salida

### 1. UFC_324_Fighter_Analysis.xlsx
Archivo Excel con múltiples hojas:
- **RESUMEN UFC 324:** Tabla resumen de todos los peleadores
- **Una hoja por peleador:** Historial detallado y estadísticas

### 2. UFC_324_Fighter_Analysis.csv
Archivo CSV con todos los datos en formato plano, ideal para análisis adicional.

## Lista Completa de Peleadores - UFC 324

### MAIN CARD (9:00 PM ET)
| # | Pelea | Categoría |
|---|-------|-----------|
| 1 | Justin Gaethje (26-5-0) vs Paddy Pimblett (23-3-0) | Lightweight |
| 2 | Sean O'Malley (18-3-0, 1NC) vs Song Yadong (22-8-1, 1NC) | Bantamweight |
| 3 | Waldo Cortes-Acosta (16-2-0) vs Derrick Lewis (29-12-0, 1NC) | Heavyweight |
| 4 | Natalia Silva (19-5-1) vs Rose Namajunas (15-7-0) | Women's Flyweight |
| 5 | Arnold Allen (20-3-0) vs Jean Silva (16-3-0) | Featherweight |

### PRELIMINARY CARD (7:00 PM ET)
| # | Pelea | Categoría |
|---|-------|-----------|
| 6 | Umar Nurmagomedov (19-1-0) vs Deiveson Figueiredo (25-5-1) | Bantamweight |
| 7 | Ateba Gautier (9-1-0) vs Andrey Pulyaev (10-3-0) | Middleweight |
| 8 | Nikita Krylov (30-11-0) vs Modestas Bukauskas (19-6-0) | Light Heavyweight |
| 9 | Alex Perez (25-10-0) vs Charles Johnson (18-7-0) | Flyweight |

### EARLY PRELIMS (5:30 PM ET)
| # | Pelea | Categoría |
|---|-------|-----------|
| 10 | Michael Johnson (25-19-0) vs Alexander Hernandez (18-8-0) | Lightweight |
| 11 | Josh Hokit (7-0-0) vs Denzel Freeman (7-1-0) | Heavyweight |
| 12 | Adam Fugitt (10-5-0) vs Ty Miller (6-0-0, 1NC) | Welterweight |
| 13 | Ricky Turcios (13-5-0) vs Cameron Smotherman (12-6-0) | Bantamweight (CANCELADA) |

## Fuentes de Datos

El script soporta múltiples fuentes:

1. **UFC Stats** (http://www.ufcstats.com) - Fuente primaria
2. **Sherdog** (https://www.sherdog.com) - Fuente de respaldo
3. **Datos Demo** - Para pruebas sin conexión

## Manejo de Errores

- Si un peleador tiene menos de 5 peleas, se procesan todas las disponibles
- Si falla el web scraping, se utilizan datos demo de respaldo
- Logs detallados de cualquier error encontrado
- Timeouts configurables para evitar bloqueos

## Estructura del Proyecto

```
NBAscraper/
├── ufc_fighter_analysis.py    # Script principal
├── requirements_ufc.txt       # Dependencias
├── README_UFC_324.md          # Este archivo
└── [Generados]
    ├── UFC_324_Fighter_Analysis.xlsx
    └── UFC_324_Fighter_Analysis.csv
```

## Ejemplo de Salida

```
======================================================================
UFC 324 FIGHTER ANALYSIS SCRIPT
24 de Enero 2026 - Análisis de Últimas 5 Peleas
======================================================================

Procesando 26 peleadores...

[1/26] Justin Gaethje... ✓ (5 peleas encontradas)
[2/26] Paddy Pimblett... ✓ (5 peleas encontradas)
...

======================================================================
RESUMEN DE ANÁLISIS
======================================================================

Peleador                 Win Rate     Racha           Finish Rate
----------------------------------------------------------------------
Justin Gaethje           60.0%        1L (L-W-W-W-L)  66.7%
Paddy Pimblett          100.0%        5W (W-W-W-W-W)  60.0%
Sean O'Malley            60.0%        1L (L-W-W-W-NC) 66.7%
...

======================================================================
ANÁLISIS COMPLETADO
======================================================================
```

## Personalización

### Agregar Más Peleadores

Edita la lista `UFC_324_FIGHTERS` en el script:

```python
UFC_324_FIGHTERS = [
    Fighter("Nombre del Peleador", "Récord", "Categoría", "Card Position", numero_pelea, "Nombre Oponente"),
    # ... más peleadores
]
```

### Cambiar Número de Peleas a Analizar

Modifica el parámetro `limit` en las funciones de scraping:

```python
fights = scraper.get_fighter_fights(profile_url, limit=10)  # Últimas 10 peleas
```

## Notas Importantes

1. El web scraping respeta los términos de servicio de los sitios
2. Se incluyen delays entre requests para no sobrecargar los servidores
3. Los datos demo son representativos pero pueden no reflejar resultados reales actualizados
4. Para datos en tiempo real, use la opción `--scrape`

## Licencia

Este script es para uso educativo y de análisis personal.

## Autor

UFC Analysis Script - Enero 2026
