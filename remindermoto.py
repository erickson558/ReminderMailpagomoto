"""
remindermoto.py — Punto de entrada de ReminderMailpagomoto.

Inicializa el sistema de logging (archivo + consola) y lanza la GUI.
La lógica de negocio vive en src/backend/; la interfaz en src/frontend/.
"""
import logging
import os
import sys
import tkinter as tk

# ---------------------------------------------------------------------------
# Logging: escribe en reminder.log junto al ejecutable (o script) y en stdout.
# El archivo de log es útil para depurar cuando corre como .exe programado.
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    log_dir = os.path.dirname(sys.executable)
else:
    log_dir = os.path.dirname(os.path.abspath(__file__))

log_path = os.path.join(log_dir, "reminder.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Importar y lanzar la GUI
# ---------------------------------------------------------------------------
from src.frontend.app import ReminderApp   # noqa: E402 (después del logging setup)


def main() -> None:
    """Crea la ventana raíz tkinter y pasa el control a ReminderApp."""
    logger.info("Iniciando ReminderMailpagomoto")
    root = tk.Tk()
    ReminderApp(root)
    root.mainloop()
    logger.info("Aplicación cerrada.")


if __name__ == "__main__":
    main()
