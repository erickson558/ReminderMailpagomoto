"""
email_sender.py — Módulo de envío de correos con soporte dual.

Métodos soportados:
  1. Outlook (win32com)  — requiere Outlook Desktop instalado en Windows.
  2. SMTP directo        — funciona con Hotmail, Gmail u cualquier proveedor SMTP.
                           Soluciona el error al enviar desde cuentas Hotmail que
                           fallan con win32com por autenticación OAuth2 moderna.

Flujo principal:
    send_email(config, destinatarios, asunto, cuerpo)
    └── Según config["send_method"]:
        ├── "smtp"    → send_via_smtp(...)
        └── "outlook" → send_via_outlook(...)
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def _normalize_recipients(recipients: list[str]) -> list[str]:
    """Elimina vacíos y duplicados sin descartar explícitamente al remitente."""
    normalized: list[str] = []
    seen: set[str] = set()

    for recipient in recipients:
        cleaned = recipient.strip()
        if not cleaned:
            continue

        recipient_key = cleaned.lower()
        if recipient_key in seen:
            continue

        seen.add(recipient_key)
        normalized.append(cleaned)

    return normalized


# ---------------------------------------------------------------------------
# Obtener cuentas Outlook disponibles
# ---------------------------------------------------------------------------

def get_outlook_accounts() -> list[str]:
    """
    Devuelve la lista de direcciones SMTP de las cuentas configuradas en Outlook.
    Si Outlook no está instalado o no hay cuentas, retorna lista vacía.
    """
    try:
        import win32com.client as win32  # Solo disponible en Windows con pywin32
        outlook = win32.Dispatch("Outlook.Application")
        accounts = outlook.Session.Accounts
        return [account.SmtpAddress for account in accounts]
    except Exception as exc:
        logger.warning("No se pudo acceder a Outlook para listar cuentas: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Método 1: Envío via Outlook (win32com / MAPI)
# ---------------------------------------------------------------------------

def send_via_outlook(sender_email: str, recipients: list[str],
                     subject: str, body: str) -> None:
    """
    Envía un correo usando Outlook mediante la interfaz MAPI (win32com).

    Requiere Outlook Desktop instalado y la cuenta configurada.
    Conserva cualquier destinatario explícitamente configurado, aunque coincida
    con la cuenta de envío.

    Args:
        sender_email: Dirección SMTP de la cuenta de envío en Outlook.
        recipients:   Lista de destinatarios (el remitente es excluido si aparece).
        subject:      Asunto del correo.
        body:         Cuerpo en texto plano.

    Raises:
        RuntimeError: Si pywin32 no está instalado, la cuenta no existe,
                      o Outlook devuelve un error.
    """
    try:
        import pythoncom
        import win32com.client as win32
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 no está instalado. Instálelo con: pip install pywin32"
        ) from exc

    pythoncom.CoInitialize()
    try:
        outlook = win32.Dispatch("Outlook.Application")
        mail = outlook.CreateItem(0)  # 0 = olMailItem (correo estándar)
        mail.Subject = subject
        mail.Body = body

        # Seleccionar cuenta de envío específica dentro de las cuentas Outlook
        if sender_email:
            account_found = False
            for account in outlook.Session.Accounts:
                if account.SmtpAddress.lower() == sender_email.lower():
                    mail.SendUsingAccount = account
                    account_found = True
                    break
            if not account_found:
                raise RuntimeError(
                    f"La cuenta '{sender_email}' no está configurada en Outlook."
                )

        normalized_recipients = _normalize_recipients(recipients)
        if not normalized_recipients:
            raise RuntimeError("No hay destinatarios válidos configurados.")

        mail.To = "; ".join(normalized_recipients)

        mail.Send()
        logger.info(
            "Correo enviado via Outlook desde '%s' a %s",
            sender_email,
            normalized_recipients,
        )

    except Exception as exc:
        raise RuntimeError(f"Error al enviar via Outlook: {exc}") from exc
    finally:
        pythoncom.CoUninitialize()


# ---------------------------------------------------------------------------
# Método 2: Envío via SMTP directo (fix para Hotmail y otros proveedores)
# ---------------------------------------------------------------------------

def send_via_smtp(sender_email: str, password: str, recipients: list[str],
                  subject: str, body: str,
                  smtp_host: str = "smtp-mail.outlook.com",
                  smtp_port: int = 587) -> None:
    """
    Envía un correo via SMTP con STARTTLS.

    Este método resuelve el problema de envío desde cuentas Hotmail/Outlook.com
    que fallan con win32com cuando usan autenticación moderna (OAuth2).

    Configuración para proveedores comunes:
        Hotmail/Outlook.com : host='smtp-mail.outlook.com', port=587
        Gmail               : host='smtp.gmail.com',        port=587
        Yahoo               : host='smtp.mail.yahoo.com',   port=587

    Para cuentas con 2FA activo se requiere una "Contraseña de aplicación":
        Hotmail: account.microsoft.com → Seguridad → Contraseñas de aplicación

    Args:
        sender_email: Dirección de correo del remitente.
        password:     Contraseña o Contraseña de aplicación.
        recipients:   Lista de destinatarios.
        subject:      Asunto del correo.
        body:         Cuerpo en texto plano.
        smtp_host:    Servidor SMTP (default: Hotmail/Outlook.com).
        smtp_port:    Puerto SMTP (default: 587 STARTTLS).

    Raises:
        RuntimeError: Con mensaje descriptivo para autenticación fallida,
                      error de conexión, o cualquier otro error SMTP.
    """
    if not sender_email:
        raise RuntimeError("Debe ingresar el correo SMTP en la configuración.")
    if not password:
        raise RuntimeError("Debe ingresar la contraseña SMTP en la configuración.")

    normalized_recipients = _normalize_recipients(recipients)
    if not normalized_recipients:
        raise RuntimeError("No hay destinatarios válidos configurados.")

    # Construir mensaje MIME con codificación UTF-8 para soporte de tildes/eñes
    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = ", ".join(normalized_recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()   # Inicia cifrado TLS sobre la conexión existente
            server.ehlo()       # Volver a saludar tras negociar TLS
            server.login(sender_email, password)
            server.sendmail(sender_email, normalized_recipients, msg.as_string())

        logger.info(
            "Correo enviado via SMTP desde '%s' a %s",
            sender_email,
            normalized_recipients,
        )

    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            "Error de autenticación SMTP.\n"
            "Verifique su correo y contraseña.\n"
            "Si tiene 2FA activo, use una Contraseña de aplicación."
        ) from exc
    except smtplib.SMTPConnectError as exc:
        raise RuntimeError(
            f"No se pudo conectar al servidor SMTP {smtp_host}:{smtp_port}.\n"
            "Verifique su conexión a internet y los datos del servidor."
        ) from exc
    except smtplib.SMTPException as exc:
        raise RuntimeError(f"Error SMTP: {exc}") from exc
    except OSError as exc:
        raise RuntimeError(
            f"Error de red al conectar a {smtp_host}:{smtp_port}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Punto de entrada unificado
# ---------------------------------------------------------------------------

def send_email(config: dict, recipients: list[str], subject: str, body: str) -> None:
    """
    Envía el correo usando el método configurado (Outlook o SMTP).

    Lee config['send_method'] para decidir qué función llamar.
    El asunto y cuerpo deben llegar ya con placeholders reemplazados.

    Args:
        config:     Diccionario de configuración completo (de load_config()).
        recipients: Lista de destinatarios.
        subject:    Asunto listo para enviar.
        body:       Cuerpo listo para enviar.
    """
    method = config.get("send_method", "outlook")

    if method == "smtp":
        smtp_cfg = config.get("smtp", {})
        send_via_smtp(
            sender_email=smtp_cfg.get("email", ""),
            password=smtp_cfg.get("password", ""),
            recipients=recipients,
            subject=subject,
            body=body,
            smtp_host=smtp_cfg.get("host", "smtp-mail.outlook.com"),
            smtp_port=int(smtp_cfg.get("port", 587)),
        )
    else:
        # Método Outlook (win32com / MAPI)
        send_via_outlook(
            sender_email=config.get("cuenta_outlook", ""),
            recipients=recipients,
            subject=subject,
            body=body,
        )
