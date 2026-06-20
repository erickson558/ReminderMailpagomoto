"""
config_manager.py — Gestión centralizada de configuración.

Lee y escribe config.json en la misma carpeta que el ejecutable (o el script).
Aplica valores por defecto para claves que no existen todavía en el archivo.
"""
import json
import os
import sys

# ---------------------------------------------------------------------------
# Ruta base: funciona en modo script (dev) y en ejecutable PyInstaller (.exe)
# ---------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    # Ejecutable compilado: usar carpeta del .exe
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # Modo desarrollo: subir dos niveles desde src/backend/
    BASE_PATH = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

CONFIG_FILE_PATH = os.path.join(BASE_PATH, "config.json")

# ---------------------------------------------------------------------------
# Valores por defecto: cualquier clave ausente se rellena con estos valores.
# Incluye la nueva sección "smtp" para envío directo con Hotmail/Gmail.
# ---------------------------------------------------------------------------
DEFAULT_CONFIG: dict = {
    "destinatarios": [],
    "asunto": "",
    "cuerpo": "",
    "auto_close": True,
    "auto_close_delay": 60,
    "send_method": "outlook",       # "outlook" | "smtp"
    "smtp": {
        "host": "smtp-mail.outlook.com",
        "port": 587,
        "email": "",
        "password": "",             # Contraseña o App Password si 2FA activo
    },
    "cuenta_outlook": "",           # Dirección SMTP de la cuenta Outlook activa
    "idioma": "es",                 # "es" | "en"
}


def load_config() -> dict:
    """
    Carga config.json. Si no existe devuelve los defaults.
    Para dicts anidados (ej: 'smtp') aplica defaults en cada sub-clave.
    """
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    # Aplicar defaults en primer nivel
    for key, default_value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = default_value
        elif isinstance(default_value, dict):
            # Rellenar sub-claves faltantes dentro de dicts anidados
            for sub_key, sub_default in default_value.items():
                config[key].setdefault(sub_key, sub_default)

    return config


def save_config(config: dict) -> None:
    """
    Guarda el dict de configuración en config.json con sangría legible.
    Lanza RuntimeError si no puede escribir el archivo.
    """
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except OSError as exc:
        raise RuntimeError(f"No se pudo guardar configuración: {exc}") from exc
