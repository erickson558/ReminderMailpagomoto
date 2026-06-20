"""
app.py — Interfaz gráfica principal de ReminderMailpagomoto.

Responsabilidades de esta clase:
  - Construir y mostrar la ventana tkinter
  - Leer/escribir estado de la UI ↔ config.json (via backend)
  - Disparar el envío en un hilo separado (GUI nunca se congela)
  - Soportar cambio de idioma en caliente (ES / EN)
  - Mostrar botón de donación PayPal

Separación de responsabilidades:
  - La lógica de envío vive en src/backend/email_sender.py
  - La lógica de configuración vive en src/backend/config_manager.py
  - Los placeholders de fecha viven en src/backend/date_utils.py
  - Las cadenas de texto viven en src/i18n/{es,en}.json
"""
import os
import sys
import threading
import logging
import webbrowser
import tkinter as tk
from tkinter import simpledialog, ttk

from src.backend.config_manager import CONFIG_FILE_PATH, load_config, save_config
from src.backend.email_sender import get_outlook_accounts, send_email
from src.backend.date_utils import replace_placeholders
from src.i18n import get_strings, LANGUAGES

logger = logging.getLogger(__name__)

# URL del botón de donación (PayPal)
DONATE_URL = "https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN"


class ReminderApp:
    """
    Ventana principal de la aplicación.

    Se construye llamando a ReminderApp(root) donde root es un tk.Tk().
    El auto-envío se dispara 1 segundo después del mainloop para respetar
    el comportamiento original del proyecto.
    """

    def __init__(self, root: tk.Tk) -> None:
        # ---- Estado central ------------------------------------------------
        self.root = root
        self.config = load_config()                         # dict de configuración
        self.lang = self.config.get("idioma", "es")         # código de idioma activo
        self.strings = get_strings(self.lang)               # cadenas de texto actuales
        self._startup_refresh_attempts = 0

        # ---- Construcción de la interfaz ------------------------------------
        self._setup_window()
        self._build_ui()
        self._load_config_to_widgets()
        self._on_method_change()        # Mostrar/ocultar secciones según método guardado
        logger.info(
            "Config inicial cargada desde %s (destinatarios=%s, asunto=%r, cuerpo_len=%s)",
            CONFIG_FILE_PATH,
            len(self.config.get("destinatarios", [])),
            self.config.get("asunto", ""),
            len(self.config.get("cuerpo", "")),
        )
        self.root.after(250, self._refresh_config_from_disk_if_widgets_empty)

        # ---- Auto-envío 1 s después de iniciar (comportamiento original) ---
        self.root.after(1000, self._auto_send)

    # =========================================================================
    # Configuración de ventana
    # =========================================================================

    def _setup_window(self) -> None:
        """Aplica título, ícono y tamaño mínimo a la ventana raíz."""
        self.root.title(self.strings["title"])
        self.root.resizable(True, True)
        self.root.minsize(520, 600)

        # Ícono: buscar reminderagua.ico en la carpeta base del proyecto
        ico = self._find_asset("reminderagua.ico")
        if ico:
            try:
                self.root.iconbitmap(ico)
            except Exception:
                pass    # Si falla (ej: formato incompatible) continuar sin ícono

    def _find_asset(self, filename: str) -> str | None:
        """
        Busca un archivo de recurso en la carpeta base del proyecto.
        Funciona tanto en modo script como en ejecutable PyInstaller.
        """
        if getattr(sys, "frozen", False):
            # Ejecutable: los assets están junto al .exe
            base = os.path.dirname(sys.executable)
        else:
            # Desarrollo: subir dos niveles desde src/frontend/
            base = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        path = os.path.join(base, filename)
        return path if os.path.exists(path) else None

    # =========================================================================
    # Construcción de la UI
    # =========================================================================

    def _build_ui(self) -> None:
        """
        Construye todos los widgets de la interfaz.

        Estructura visual:
          [Barra superior: idioma + botón donación]
          [Frame: Destinatarios + botones Agregar/Eliminar]
          [Asunto]
          [Cuerpo del correo]
          [Frame: Método de Envío (Outlook | SMTP)]
          [Frame: Cierre Automático]
          [Botones: Enviar | Guardar | Salir]
          [Barra de estado]
        """
        s = self.strings   # alias corto para las cadenas de texto

        # ----- Barra superior: idioma + donación ----------------------------
        bar = tk.Frame(self.root, pady=4)
        bar.pack(fill=tk.X, padx=10)

        tk.Label(bar, text=s["language_label"]).pack(side=tk.LEFT)

        self.lang_var = tk.StringVar(value=self.lang)
        # La combobox muestra los códigos ("es", "en"); cambia idioma al seleccionar
        lang_combo = ttk.Combobox(
            bar, textvariable=self.lang_var,
            values=list(LANGUAGES.keys()), state="readonly", width=5,
        )
        lang_combo.pack(side=tk.LEFT, padx=(4, 0))
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        # Etiqueta de idioma (ej: "Español") junto al combo
        self.lang_name_lbl = tk.Label(bar, text=LANGUAGES.get(self.lang, ""))
        self.lang_name_lbl.pack(side=tk.LEFT, padx=(4, 0))

        # Botón de donación (abre PayPal en el navegador)
        self.btn_donate = tk.Button(
            bar, text=s["btn_donate"],
            fg="#0070ba", cursor="hand2",
            relief=tk.FLAT, font=("Arial", 9, "bold"),
            command=self._open_donate,
        )
        self.btn_donate.pack(side=tk.RIGHT, padx=5)

        # ----- Sección: Destinatarios ---------------------------------------
        self.frame_dest = tk.LabelFrame(self.root, text=s["recipients_frame"])
        self.frame_dest.pack(padx=10, pady=5, fill=tk.BOTH)

        self.listbox_destinatarios = tk.Listbox(
            self.frame_dest, width=60, height=4, selectmode=tk.EXTENDED,
        )
        self.listbox_destinatarios.pack(padx=10, pady=(5, 0), fill=tk.X)

        btn_dest = tk.Frame(self.frame_dest)
        btn_dest.pack(pady=5)
        self.btn_agregar = tk.Button(
            btn_dest, text=s["add"], width=15, command=self._agregar_destinatario,
        )
        self.btn_agregar.pack(side=tk.LEFT, padx=5)
        self.btn_eliminar = tk.Button(
            btn_dest, text=s["remove"], width=15, command=self._eliminar_destinatario,
        )
        self.btn_eliminar.pack(side=tk.LEFT, padx=5)

        # ----- Asunto -------------------------------------------------------
        frame_asunto = tk.Frame(self.root)
        frame_asunto.pack(padx=10, pady=(5, 0), fill=tk.X)
        self.lbl_asunto = tk.Label(frame_asunto, text=s["subject_label"])
        self.lbl_asunto.pack(anchor="w")
        self.entry_asunto = tk.Entry(frame_asunto, width=65)
        self.entry_asunto.pack(fill=tk.X, pady=(2, 5))

        # ----- Cuerpo -------------------------------------------------------
        frame_cuerpo = tk.Frame(self.root)
        frame_cuerpo.pack(padx=10, pady=(0, 5), fill=tk.BOTH)
        self.lbl_cuerpo = tk.Label(frame_cuerpo, text=s["body_label"])
        self.lbl_cuerpo.pack(anchor="w")
        self.text_cuerpo = tk.Text(frame_cuerpo, width=65, height=5)
        self.text_cuerpo.pack(fill=tk.BOTH, pady=(2, 0))

        # ----- Método de Envío ----------------------------------------------
        self.frame_metodo = tk.LabelFrame(self.root, text=s["send_method_frame"])
        self.frame_metodo.pack(padx=10, pady=5, fill=tk.BOTH)

        self.send_method_var = tk.StringVar(
            value=self.config.get("send_method", "outlook")
        )

        # Radio: Outlook
        self.rb_outlook = tk.Radiobutton(
            self.frame_metodo, text=s["method_outlook"],
            value="outlook", variable=self.send_method_var,
            command=self._on_method_change,
        )
        self.rb_outlook.grid(row=0, column=0, sticky="w", padx=10, pady=(6, 2))

        # Sub-frame Outlook (combobox de cuentas)
        self.frame_outlook_cfg = tk.Frame(self.frame_metodo)
        self.frame_outlook_cfg.grid(row=0, column=1, sticky="w", padx=10, pady=(6, 2))
        self.lbl_cuenta = tk.Label(self.frame_outlook_cfg, text=s["select_account"])
        self.lbl_cuenta.pack(side=tk.LEFT)
        cuentas = get_outlook_accounts()
        self.combobox_cuenta = ttk.Combobox(
            self.frame_outlook_cfg, values=cuentas, state="readonly", width=32,
        )
        self.combobox_cuenta.pack(side=tk.LEFT, padx=5)

        # Radio: SMTP
        self.rb_smtp = tk.Radiobutton(
            self.frame_metodo, text=s["method_smtp"],
            value="smtp", variable=self.send_method_var,
            command=self._on_method_change,
        )
        self.rb_smtp.grid(row=1, column=0, sticky="w", padx=10, pady=(2, 2))

        # Sub-frame SMTP (email, password, host, port)
        self.frame_smtp_cfg = tk.Frame(self.frame_metodo)
        self.frame_smtp_cfg.grid(row=1, column=1, sticky="w", padx=10, pady=(2, 2))

        smtp_cfg = self.config.get("smtp", {})

        self.lbl_smtp_email = tk.Label(self.frame_smtp_cfg, text=s["smtp_email"])
        self.lbl_smtp_email.grid(row=0, column=0, sticky="e", padx=4, pady=2)
        self.entry_smtp_email = tk.Entry(self.frame_smtp_cfg, width=30)
        self.entry_smtp_email.insert(0, smtp_cfg.get("email", ""))
        self.entry_smtp_email.grid(row=0, column=1, columnspan=3, sticky="w", pady=2)

        self.lbl_smtp_pass = tk.Label(self.frame_smtp_cfg, text=s["smtp_password"])
        self.lbl_smtp_pass.grid(row=1, column=0, sticky="e", padx=4, pady=2)
        self.entry_smtp_pass = tk.Entry(self.frame_smtp_cfg, width=30, show="*")
        self.entry_smtp_pass.insert(0, smtp_cfg.get("password", ""))
        self.entry_smtp_pass.grid(row=1, column=1, columnspan=3, sticky="w", pady=2)

        self.lbl_smtp_host = tk.Label(self.frame_smtp_cfg, text=s["smtp_host"])
        self.lbl_smtp_host.grid(row=2, column=0, sticky="e", padx=4, pady=2)
        self.entry_smtp_host = tk.Entry(self.frame_smtp_cfg, width=22)
        self.entry_smtp_host.insert(0, smtp_cfg.get("host", "smtp-mail.outlook.com"))
        self.entry_smtp_host.grid(row=2, column=1, sticky="w", padx=(0, 6), pady=2)

        self.lbl_smtp_port = tk.Label(self.frame_smtp_cfg, text=s["smtp_port"])
        self.lbl_smtp_port.grid(row=2, column=2, sticky="e", padx=4, pady=2)
        self.entry_smtp_port = tk.Entry(self.frame_smtp_cfg, width=6)
        self.entry_smtp_port.insert(0, str(smtp_cfg.get("port", 587)))
        self.entry_smtp_port.grid(row=2, column=3, sticky="w", pady=2)

        # Hint SMTP (servidores comunes)
        self.lbl_smtp_hint = tk.Label(
            self.frame_smtp_cfg, text=s["smtp_hint"],
            fg="gray", font=("Arial", 8),
        )
        self.lbl_smtp_hint.grid(row=3, column=0, columnspan=4, sticky="w", padx=4, pady=(0, 4))

        # ----- Cierre Automático --------------------------------------------
        self.frame_autoclose = tk.LabelFrame(self.root, text=s["auto_close_frame"])
        self.frame_autoclose.pack(padx=10, pady=5, fill=tk.X)

        self.auto_close_var = tk.BooleanVar(value=self.config.get("auto_close", True))
        self.chk_auto_close = tk.Checkbutton(
            self.frame_autoclose,
            text=s["auto_close_check"],
            variable=self.auto_close_var,
        )
        self.chk_auto_close.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.lbl_delay = tk.Label(self.frame_autoclose, text=s["auto_close_delay"])
        self.lbl_delay.grid(row=1, column=0, sticky="w", padx=10)
        self.auto_close_delay_var = tk.StringVar(
            value=str(self.config.get("auto_close_delay", 60))
        )
        self.entry_delay = tk.Entry(
            self.frame_autoclose, textvariable=self.auto_close_delay_var, width=8,
        )
        self.entry_delay.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        # ----- Botones principales ------------------------------------------
        frame_btns = tk.Frame(self.root)
        frame_btns.pack(pady=8)

        self.btn_enviar = tk.Button(
            frame_btns, text=s["btn_send"], width=18, command=self._enviar_correo,
        )
        self.btn_enviar.pack(side=tk.LEFT, padx=5)

        self.btn_guardar = tk.Button(
            frame_btns, text=s["btn_save"], width=18, command=self._save_config_from_ui,
        )
        self.btn_guardar.pack(side=tk.LEFT, padx=5)

        self.btn_salir = tk.Button(
            frame_btns, text=s["btn_exit"], width=12, command=self.root.destroy,
        )
        self.btn_salir.pack(side=tk.LEFT, padx=5)

        # ----- Barra de estado (parte inferior) -----------------------------
        self.status_label = tk.Label(
            self.root, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W, pady=3,
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    # =========================================================================
    # Carga de configuración en widgets
    # =========================================================================

    def _load_config_to_widgets(self) -> None:
        """
        Rellena los widgets con los valores guardados en config.json.
        Se llama una vez después de construir la UI.
        """
        self._apply_config_to_widgets(self.config)

    def _apply_config_to_widgets(self, config: dict) -> None:
        """Sincroniza los widgets editables con el contenido de config."""
        self.listbox_destinatarios.delete(0, tk.END)

        # Destinatarios
        for dest in config.get("destinatarios", []):
            self.listbox_destinatarios.insert(tk.END, dest)

        # Asunto y cuerpo
        self.entry_asunto.delete(0, tk.END)
        self.entry_asunto.insert(0, config.get("asunto", ""))
        self.text_cuerpo.delete("1.0", tk.END)
        self.text_cuerpo.insert("1.0", config.get("cuerpo", ""))

        # Cuenta Outlook guardada
        saved_account = config.get("cuenta_outlook", "")
        cuentas = self.combobox_cuenta["values"]
        if cuentas:
            if saved_account in cuentas:
                self.combobox_cuenta.set(saved_account)
            else:
                self.combobox_cuenta.current(0)

    def _refresh_config_from_disk_if_widgets_empty(self) -> None:
        """
        Reintenta la carga desde disco si la UI quedó vacía al arrancar.

        Esto cubre escenarios donde el .exe inicia antes de que el archivo de
        configuración quede visible en el directorio sincronizado.
        """
        self._startup_refresh_attempts += 1

        if self.listbox_destinatarios.size() > 0:
            return
        if self.entry_asunto.get().strip() or self.text_cuerpo.get("1.0", tk.END).strip():
            return

        refreshed_config = load_config()
        has_content = bool(
            refreshed_config.get("destinatarios")
            or refreshed_config.get("asunto", "").strip()
            or refreshed_config.get("cuerpo", "").strip()
        )
        if not has_content:
            logger.info(
                "Reintento %s sin contenido util desde: %s",
                self._startup_refresh_attempts,
                CONFIG_FILE_PATH,
            )
            if self._startup_refresh_attempts < 20:
                self.root.after(250, self._refresh_config_from_disk_if_widgets_empty)
            return

        self.config = refreshed_config
        self._apply_config_to_widgets(refreshed_config)
        logger.info(
            "Config recargada desde disco al iniciar: %s (destinatarios=%s, intento=%s)",
            CONFIG_FILE_PATH,
            len(refreshed_config.get("destinatarios", [])),
            self._startup_refresh_attempts,
        )

    # =========================================================================
    # Cambio de idioma
    # =========================================================================

    def _on_language_change(self, _event=None) -> None:
        """
        Cambia el idioma de la interfaz al seleccionar uno nuevo en el combo.
        Actualiza todos los textos de la UI en caliente sin reiniciar la app.
        """
        new_lang = self.lang_var.get()
        if new_lang == self.lang:
            return
        self.lang = new_lang
        self.strings = get_strings(new_lang)
        self._apply_strings()

    def _apply_strings(self) -> None:
        """
        Aplica las cadenas de texto del idioma activo a todos los widgets.
        Llamar después de cambiar self.strings.
        """
        s = self.strings
        self.root.title(s["title"])
        self.lang_name_lbl.config(text=LANGUAGES.get(self.lang, ""))
        self.btn_donate.config(text=s["btn_donate"])
        self.frame_dest.config(text=s["recipients_frame"])
        self.btn_agregar.config(text=s["add"])
        self.btn_eliminar.config(text=s["remove"])
        self.lbl_asunto.config(text=s["subject_label"])
        self.lbl_cuerpo.config(text=s["body_label"])
        self.frame_metodo.config(text=s["send_method_frame"])
        self.rb_outlook.config(text=s["method_outlook"])
        self.rb_smtp.config(text=s["method_smtp"])
        self.lbl_cuenta.config(text=s["select_account"])
        self.lbl_smtp_email.config(text=s["smtp_email"])
        self.lbl_smtp_pass.config(text=s["smtp_password"])
        self.lbl_smtp_host.config(text=s["smtp_host"])
        self.lbl_smtp_port.config(text=s["smtp_port"])
        self.lbl_smtp_hint.config(text=s["smtp_hint"])
        self.frame_autoclose.config(text=s["auto_close_frame"])
        self.chk_auto_close.config(text=s["auto_close_check"])
        self.lbl_delay.config(text=s["auto_close_delay"])
        self.btn_enviar.config(text=s["btn_send"])
        self.btn_guardar.config(text=s["btn_save"])
        self.btn_salir.config(text=s["btn_exit"])

    # =========================================================================
    # Mostrar / ocultar sección SMTP vs Outlook
    # =========================================================================

    def _on_method_change(self) -> None:
        """
        Muestra la sección de configuración correspondiente al método seleccionado.
        La sección del método no activo se oculta para no confundir al usuario.
        """
        if self.send_method_var.get() == "smtp":
            self.frame_smtp_cfg.grid()       # Mostrar configuración SMTP
            self.frame_outlook_cfg.grid_remove()  # Ocultar configuración Outlook
        else:
            self.frame_outlook_cfg.grid()    # Mostrar configuración Outlook
            self.frame_smtp_cfg.grid_remove()     # Ocultar configuración SMTP

    # =========================================================================
    # Leer config de los widgets
    # =========================================================================

    def _get_config_from_ui(self) -> dict:
        """
        Lee el estado actual de todos los widgets y construye el dict de config.
        Este dict es el que se guarda en config.json o se pasa al backend.
        """
        try:
            auto_delay = int(self.auto_close_delay_var.get())
        except (ValueError, TypeError):
            auto_delay = 60   # Fallback si el campo tiene texto inválido

        try:
            smtp_port = int(self.entry_smtp_port.get().strip())
        except (ValueError, TypeError):
            smtp_port = 587

        return {
            "destinatarios": list(self.listbox_destinatarios.get(0, tk.END)),
            "asunto": self.entry_asunto.get().strip(),
            "cuerpo": self.text_cuerpo.get("1.0", tk.END).strip(),
            "auto_close": self.auto_close_var.get(),
            "auto_close_delay": auto_delay,
            "send_method": self.send_method_var.get(),
            "smtp": {
                "host": self.entry_smtp_host.get().strip(),
                "port": smtp_port,
                "email": self.entry_smtp_email.get().strip(),
                "password": self.entry_smtp_pass.get(),
            },
            "cuenta_outlook": self.combobox_cuenta.get(),
            "idioma": self.lang,
        }

    def _persist_config(self, config: dict | None = None) -> dict:
        """Guarda el estado actual de la UI y actualiza el snapshot en memoria."""
        config_to_save = config or self._get_config_from_ui()
        save_config(config_to_save)
        self.config = config_to_save
        return config_to_save

    # =========================================================================
    # Guardar configuración
    # =========================================================================

    def _save_config_from_ui(self) -> None:
        """Lee la UI, construye el dict de config y lo escribe en config.json."""
        try:
            self._persist_config()
            self._set_status(self.strings["status_saved"], "green")
        except Exception as exc:
            self._set_status(self.strings["status_save_error"] + str(exc), "red")

    # =========================================================================
    # Barra de estado (thread-safe)
    # =========================================================================

    def _set_status(self, message: str, color: str = "black") -> None:
        """
        Actualiza la barra de estado de forma thread-safe.
        Se puede llamar desde hilos secundarios (after garantiza ejecución en main thread).
        """
        self.root.after(0, lambda: self.status_label.config(text=message, fg=color))

    # =========================================================================
    # Acciones de destinatarios
    # =========================================================================

    def _agregar_destinatario(self) -> None:
        """Abre un diálogo para que el usuario ingrese un correo y lo agrega a la lista."""
        nuevo = simpledialog.askstring(
            self.strings["dlg_add_title"],
            self.strings["dlg_add_prompt"],
            parent=self.root,
        )
        if nuevo and nuevo.strip():
            self.listbox_destinatarios.insert(tk.END, nuevo.strip())
            try:
                self._persist_config()
                self._set_status(self.strings["status_added"], "green")
            except Exception as exc:
                self._set_status(self.strings["status_save_error"] + str(exc), "red")

    def _eliminar_destinatario(self) -> None:
        """Elimina los destinatarios seleccionados en la listbox."""
        seleccion = self.listbox_destinatarios.curselection()
        if not seleccion:
            self._set_status(self.strings["status_select_to_remove"], "red")
            return
        # Eliminar en orden inverso para que los índices no se desplacen
        for index in reversed(seleccion):
            self.listbox_destinatarios.delete(index)
        try:
            self._persist_config()
            self._set_status(self.strings["status_removed"], "green")
        except Exception as exc:
            self._set_status(self.strings["status_save_error"] + str(exc), "red")

    # =========================================================================
    # Botón donación
    # =========================================================================

    def _open_donate(self) -> None:
        """Abre el link de donación PayPal en el navegador predeterminado."""
        webbrowser.open(DONATE_URL)

    # =========================================================================
    # Envío de correo (con threading para no congelar la GUI)
    # =========================================================================

    def _auto_send(self) -> None:
        """
        Método disparado automáticamente 1 segundo después de iniciar la app.
        Mantiene el comportamiento original: la app envía sola al arrancar.
        """
        logger.info("Auto-envío activado al iniciar.")
        self._enviar_correo()

    def _enviar_correo(self) -> None:
        """
        Valida los datos, reemplaza placeholders y dispara el envío en un hilo.

        El hilo es daemon=True para que no bloquee el cierre de la app.
        El botón de envío se deshabilita durante el proceso y se reactiva al terminar.
        """
        s = self.strings

        # --- Validaciones previas -------------------------------------------
        destinatarios = [
            d.strip() for d in self.listbox_destinatarios.get(0, tk.END) if d.strip()
        ]
        if not destinatarios:
            self._set_status(s["status_no_recipients"], "red")
            return

        if self.send_method_var.get() == "smtp":
            if not self.entry_smtp_email.get().strip():
                self._set_status(s["status_no_smtp_email"], "red")
                return
            if not self.entry_smtp_pass.get():
                self._set_status(s["status_no_smtp_password"], "red")
                return

        # --- Reemplazar placeholders en asunto y cuerpo ---------------------
        asunto_template = self.entry_asunto.get().strip()
        cuerpo_template = self.text_cuerpo.get("1.0", tk.END).strip()
        asunto = replace_placeholders(asunto_template)
        cuerpo = replace_placeholders(cuerpo_template)
        logger.info("Asunto resuelto para envio: %s", asunto)
        logger.info("Cuerpo resuelto para envio: %s", cuerpo)

        # Tomar snapshot de config al momento de enviar (thread safety)
        config_snap = self._get_config_from_ui()
        try:
            config_snap = self._persist_config(config_snap)
        except Exception as exc:
            logger.warning("No se pudo persistir la configuración antes de enviar: %s", exc)

        # --- Deshabilitar botón y mostrar progreso --------------------------
        self.btn_enviar.config(state=tk.DISABLED)
        self._set_status(s["status_sending"], "blue")

        def do_send() -> None:
            """Función ejecutada en hilo secundario: envía el correo."""
            try:
                send_email(config_snap, destinatarios, asunto, cuerpo)
                logger.info("Correo enviado a %s", destinatarios)
                self._set_status(s["status_sent"], "green")

                # Si auto-close está activo, iniciar countdown en main thread
                if config_snap.get("auto_close", False):
                    delay = config_snap.get("auto_close_delay", 60)
                    self.root.after(0, lambda: self._iniciar_countdown(delay))

            except Exception as exc:
                logger.error("Error al enviar correo: %s", exc)
                self._set_status(s["status_error"] + str(exc), "red")
            finally:
                # Siempre re-habilitar el botón al terminar (éxito o error)
                self.root.after(0, lambda: self.btn_enviar.config(state=tk.NORMAL))

        thread = threading.Thread(target=do_send, daemon=True)
        thread.start()

    # =========================================================================
    # Countdown de cierre automático
    # =========================================================================

    def _iniciar_countdown(self, segundos: int) -> None:
        """
        Inicia la cuenta regresiva para el cierre automático de la app.
        Usa root.after() para actualizar el estado cada segundo en el main thread.
        """
        def tick(n: int) -> None:
            if n > 0:
                msg = self.strings["status_closing"].format(n=n)
                self._set_status(msg, "green")
                self.root.after(1000, lambda: tick(n - 1))
            else:
                self.root.destroy()     # Cierra la ventana principal

        tick(segundos)
