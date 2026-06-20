"""
date_utils.py — Utilidades de fecha para los placeholders del correo.

Proporciona la lógica de "mes anterior" que usa el proyecto:
    - En enero → retorna diciembre del año anterior
    - Resto del año → retorna el mes en curso (comportamiento del código original)

Placeholders soportados:
    [Mes Actual]      → nombre del mes (capitalizado) según lógica anterior
    [año en numero]   → año como string

El reemplazo es tolerante a diferencias de mayúsculas/minúsculas y a la
variante sin ñ en "ano" para evitar que plantillas válidas salgan sin sustituir.
"""
import datetime
import re

# Nombres de los meses en español (índice 1-12)
MESES_ES: dict[int, str] = {
    1: "enero",   2: "febrero",  3: "marzo",
    4: "abril",   5: "mayo",     6: "junio",
    7: "julio",   8: "agosto",   9: "septiembre",
    10: "octubre", 11: "noviembre", 12: "diciembre",
}

MONTH_PLACEHOLDER_PATTERN = re.compile(r"\[\s*mes\s+actual\s*\]", re.IGNORECASE)
YEAR_PLACEHOLDER_PATTERN = re.compile(
    r"\[\s*a(?:ñ|n)o\s+en\s+numero\s*\]",
    re.IGNORECASE,
)


def get_previous_month_info() -> tuple[str, str]:
    """
    Calcula el nombre del mes y año a usar en los placeholders.

    Lógica heredada del código original:
      - Si el mes actual es enero → mes = diciembre, año = año anterior
      - Cualquier otro mes → mes = mes actual, año = año actual

    Retorna:
        (nombre_mes_capitalizado, año_como_string)
    """
    now = datetime.datetime.now()
    month = now.month
    year = now.year

    if month == 1:
        ref_month = 12
        ref_year = year - 1
    else:
        ref_month = month
        ref_year = year

    return MESES_ES[ref_month].capitalize(), str(ref_year)


def replace_placeholders(text: str) -> str:
    """
    Reemplaza todos los placeholders conocidos en 'text'.

    Placeholders:
        [Mes Actual]    → nombre del mes de referencia (ej: "Mayo")
        [año en numero] → año de referencia (ej: "2026")

    Retorna el texto con los placeholders sustituidos.
    """
    month_name, year_str = get_previous_month_info()
    text = MONTH_PLACEHOLDER_PATTERN.sub(month_name, text)
    text = YEAR_PLACEHOLDER_PATTERN.sub(year_str, text)
    return text
