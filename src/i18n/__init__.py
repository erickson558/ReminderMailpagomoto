"""
i18n/__init__.py — Cargador de cadenas de texto para multi-idioma.

Uso:
    from src.i18n import get_strings, LANGUAGES

    strings = get_strings("es")   # Carga Español
    strings = get_strings("en")   # Carga English
    title = strings["title"]

Los archivos JSON están junto a este __init__.py (src/i18n/es.json, en.json).
Cuando la app está compilada como .exe con PyInstaller, los archivos se leen
desde sys._MEIPASS que es donde PyInstaller desempaqueta los datos.
"""
import json
import os
import sys

# Diccionario de idiomas disponibles: clave = código ISO, valor = nombre para mostrar
LANGUAGES: dict[str, str] = {
    "es": "Español",
    "en": "English",
}


def _get_i18n_dir() -> str:
    """
    Retorna la ruta al directorio de archivos de traducción.
    Maneja tanto modo script como ejecutable PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # Ejecutable compilado: PyInstaller extrae los datas a sys._MEIPASS
        return os.path.join(sys._MEIPASS, "src", "i18n")
    else:
        # Modo desarrollo: la carpeta está junto a este archivo
        return os.path.dirname(os.path.abspath(__file__))


def get_strings(lang: str) -> dict:
    """
    Carga y retorna el diccionario de cadenas de texto para el idioma 'lang'.

    Si el archivo del idioma solicitado no existe, cae de vuelta al Español.

    Args:
        lang: Código de idioma ("es", "en").

    Returns:
        Dict con todas las cadenas de texto de la interfaz.
    """
    i18n_dir = _get_i18n_dir()
    lang_file = os.path.join(i18n_dir, f"{lang}.json")

    # Si el idioma pedido no existe, usar español como fallback
    if not os.path.exists(lang_file):
        lang_file = os.path.join(i18n_dir, "es.json")

    with open(lang_file, "r", encoding="utf-8") as f:
        return json.load(f)
