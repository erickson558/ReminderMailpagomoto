"""
config_manager.py — Gestión centralizada de configuración.

Lee y escribe config.json en la misma carpeta que el ejecutable (o el script).
Aplica valores por defecto para claves que no existen todavía en el archivo.
"""
import json
import os
import sys


def _unique_paths(paths: list[str]) -> list[str]:
    """Conserva el orden original y elimina rutas repetidas."""
    unique: list[str] = []
    seen: set[str] = set()

    for path in paths:
        normalized = os.path.normcase(os.path.abspath(path))
        if normalized in seen:
            continue

        seen.add(normalized)
        unique.append(path)

    return unique


def resolve_config_file_path(
    *,
    frozen: bool,
    executable_path: str | None = None,
    source_file: str | None = None,
    cwd: str | None = None,
) -> str:
    """Resuelve qué config.json usar según el contexto de ejecución."""
    current_dir = os.path.abspath(cwd or os.getcwd())

    if frozen:
        exe_dir = os.path.dirname(os.path.abspath(executable_path or sys.executable))
        read_candidates = [exe_dir]
        default_write_dir = exe_dir
    else:
        project_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(source_file or __file__)))
        )
        read_candidates = _unique_paths([
            project_dir,
            current_dir,
        ])
        default_write_dir = project_dir

    for base_dir in read_candidates:
        candidate = os.path.join(base_dir, "config.json")
        if os.path.exists(candidate):
            return candidate

    return os.path.join(default_write_dir, "config.json")


# ---------------------------------------------------------------------------
# Ruta base: funciona en modo script (dev) y en ejecutable PyInstaller (.exe)
# ---------------------------------------------------------------------------
CONFIG_FILE_PATH = resolve_config_file_path(
    frozen=getattr(sys, 'frozen', False),
    executable_path=getattr(sys, 'executable', None),
    source_file=__file__,
)

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


def _migrate_legacy_config(config: dict) -> dict:
    """Normaliza configuraciones antiguas al esquema actual sin perder valores."""
    normalized = dict(config)

    if "email_method" in normalized and not normalized.get("send_method"):
        normalized["send_method"] = normalized["email_method"]

    if "outlook_account" in normalized and not normalized.get("cuenta_outlook"):
        normalized["cuenta_outlook"] = normalized["outlook_account"]

    if "language" in normalized and not normalized.get("idioma"):
        normalized["idioma"] = normalized["language"]

    legacy_smtp = normalized.get("smtp_config") or {}
    current_smtp = dict(normalized.get("smtp") or {})
    if legacy_smtp and not current_smtp:
        current_smtp = {
            "host": legacy_smtp.get("server", "smtp-mail.outlook.com"),
            "port": legacy_smtp.get("port", 587),
            "email": legacy_smtp.get("username", ""),
            "password": legacy_smtp.get("password", ""),
        }
    else:
        if not current_smtp.get("host") and legacy_smtp.get("server"):
            current_smtp["host"] = legacy_smtp["server"]
        if not current_smtp.get("port") and legacy_smtp.get("port"):
            current_smtp["port"] = legacy_smtp["port"]
        if not current_smtp.get("email") and legacy_smtp.get("username"):
            current_smtp["email"] = legacy_smtp["username"]
        if not current_smtp.get("password") and legacy_smtp.get("password"):
            current_smtp["password"] = legacy_smtp["password"]

    if current_smtp:
        normalized["smtp"] = current_smtp

    return normalized


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

    config = _migrate_legacy_config(config)

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
