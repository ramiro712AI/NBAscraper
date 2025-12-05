#!/usr/bin/env python3
"""
Test date parsing logic for NBA season
"""

from datetime import datetime
import re

def parse_date(date_str: str) -> str:
    """Parse ESPN date format to YYYY-MM-DD"""
    try:
        # ESPN uses formats like "Wed 12/4", "Thu 11/28", etc.
        match = re.search(r'(\d{1,2})/(\d{1,2})', date_str)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))

            # Get current date
            now = datetime.now()
            current_year = now.year
            current_month = now.month

            # NBA season logic:
            # Season runs Oct (10) - Jun (6)
            # If we're in Oct-Dec and game month is Oct-Dec: same year
            # If we're in Oct-Dec and game month is Jan-Jun: next year
            # If we're in Jan-Jun and game month is Oct-Dec: previous year
            # If we're in Jan-Jun and game month is Jan-Jun: same year
            # If we're in Jul-Sep (off-season): use previous season

            if current_month >= 10:  # Oct, Nov, Dec
                if month >= 10:  # Game in Oct-Dec
                    year = current_year
                else:  # Game in Jan-Jun (future games in next year)
                    year = current_year + 1
            elif current_month <= 6:  # Jan-Jun
                if month >= 10:  # Game in Oct-Dec (was last year)
                    year = current_year - 1
                else:  # Game in Jan-Jun (same year)
                    year = current_year
            else:  # Jul-Sep (off-season)
                # Assume looking at previous season
                if month >= 10:
                    year = current_year - 1
                else:
                    year = current_year

            return f"{year}-{month:02d}-{day:02d}"

        return date_str
    except:
        return date_str


# Test the date parsing
print("="*80)
print("PRUEBA DE LÓGICA DE FECHAS - TEMPORADA NBA")
print("="*80)

now = datetime.now()
print(f"\nFecha actual: {now.strftime('%Y-%m-%d')} (Mes: {now.month})")
print(f"Año actual: {now.year}")

test_dates = [
    "Wed 12/4",   # Diciembre
    "Thu 11/28",  # Noviembre
    "Fri 10/25",  # Octubre
    "Mon 1/15",   # Enero
    "Tue 2/20",   # Febrero
    "Wed 3/10",   # Marzo
    "Thu 4/15",   # Abril
]

print("\nResultados de conversión de fechas:")
print("-" * 80)

for date_str in test_dates:
    parsed = parse_date(date_str)
    print(f"{date_str:15} → {parsed}")

print("\n" + "="*80)
print("Lógica aplicada:")
print("="*80)

if now.month >= 10:
    print(f"✓ Estamos en Oct-Dic ({now.month})")
    print(f"  - Juegos Oct-Dic: año {now.year}")
    print(f"  - Juegos Ene-Jun: año {now.year + 1}")
elif now.month <= 6:
    print(f"✓ Estamos en Ene-Jun ({now.month})")
    print(f"  - Juegos Oct-Dic: año {now.year - 1}")
    print(f"  - Juegos Ene-Jun: año {now.year}")
else:
    print(f"✓ Estamos en temporada muerta ({now.month})")
    print(f"  - Usando temporada anterior")

print("="*80)
