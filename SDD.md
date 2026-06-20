# SDD - ReminderMailpagomoto
## Spec Driven Development Document
**Versión:** 2.4  
**Fecha:** 2026-06-20  
**Autor:** erickson558

---

## 1. Descripción del Proyecto

**ReminderMailpagomoto** es una aplicación de escritorio Windows que envía correos de recordatorio automáticos de pagos (moto, servicios, etc.) vía Outlook o SMTP directo. Se ejecuta programada vía Windows Task Scheduler.

---

## 2. Funcionalidades Core (Spec)

### 2.1 Envío de Correos
| ID | Spec | Estado |
|----|------|--------|
| EM-01 | Enviar correo vía Outlook (win32com) | ✅ Implementado |
| EM-02 | Enviar correo vía SMTP directo (Hotmail, Gmail, etc.) | ✅ v2.0 |
| EM-03 | Soporte placeholders `[Mes Actual]` y `[año en numero]` con reemplazo tolerante a mayúsculas/minúsculas y variante `ano` | ✅ v2.1 |
| EM-04 | Filtrar remitente de la lista de destinatarios | ✅ Implementado |
| EM-05 | Envío en hilo separado (no bloquea GUI) | ✅ v2.0 |

### 2.2 Gestión de Destinatarios
| ID | Spec | Estado |
|----|------|--------|
| GD-01 | Agregar destinatarios vía diálogo | ✅ Implementado |
| GD-02 | Eliminar destinatarios seleccionados | ✅ Implementado |
| GD-03 | Persistir lista en config.json | ✅ Implementado |

### 2.3 Configuración
| ID | Spec | Estado |
|----|------|--------|
| CF-01 | Guardar/cargar configuración en config.json; en `.exe` se usa el archivo ubicado junto al ejecutable | ✅ v2.3 |
| CF-06 | Compatibilidad con `config.json` legado (`email_method`, `outlook_account`, `smtp_config`, `language`) | ✅ v2.4 |
| CF-02 | Selección de cuenta Outlook | ✅ Implementado |
| CF-03 | Configuración SMTP (host, puerto, email, password) | ✅ v2.0 |
| CF-04 | Cierre automático configurable (segundos) | ✅ Implementado |
| CF-05 | Selección de idioma (ES/EN) | ✅ v2.0 |

### 2.4 Interfaz Gráfica
| ID | Spec | Estado |
|----|------|--------|
| UI-01 | Ventana principal tkinter | ✅ Implementado |
| UI-02 | Barra de estado con mensajes de color | ✅ Implementado |
| UI-03 | Multi-idioma (Español / English) | ✅ v2.0 |
| UI-04 | Botón "Cómprame una cerveza" (PayPal) | ✅ v2.0 |
| UI-05 | GUI no se congela durante envío | ✅ v2.0 |
| UI-06 | Ícono de aplicación (.ico) | ✅ Implementado |

### 2.5 Automatización
| ID | Spec | Estado |
|----|------|--------|
| AU-01 | Auto-envío 1 segundo después de iniciar | ✅ Implementado |
| AU-02 | Countdown de cierre automático post-envío | ✅ Implementado |
| AU-03 | Compatible con Windows Task Scheduler | ✅ Implementado |

### 2.6 Compilación
| ID | Spec | Estado |
|----|------|--------|
| CP-01 | Compilar a .exe sin consola | ✅ Implementado |
| CP-02 | Incluir ícono .ico en el ejecutable | ✅ Implementado |
| CP-03 | Incluir archivos i18n en el ejecutable | ✅ v2.0 |
| CP-04 | Recompilar dejando `remindermoto.exe` junto a `remindermoto.py` | ✅ v2.2 |

---

## 3. Arquitectura v2.0

```
ReminderMailpagomoto/
├── .claude/
│   ├── settings.json           # Permisos Claude Code
│   ├── agents/
│   │   └── reminder-dev.md     # Agente especializado del proyecto
│   └── commands/
│       ├── github-push.md      # /github-push
│       ├── comment-code.md     # /comment-code
│       ├── refactor-python.md  # /refactor-python
│       └── compile-exe.md      # /compile-exe
├── src/
│   ├── backend/
│   │   ├── config_manager.py   # Lectura/escritura config.json
│   │   ├── email_sender.py     # Envío Outlook + SMTP
│   │   └── date_utils.py       # Placeholders de fecha
│   ├── frontend/
│   │   └── app.py              # GUI tkinter (clase ReminderApp)
│   └── i18n/
│       ├── __init__.py         # Loader de traducciones
│       ├── es.json             # Cadenas en Español
│       └── en.json             # Cadenas en English
├── config.json                 # Configuración persistente
├── build_remindermoto.ps1      # Build reproducible a .exe en raíz del proyecto
├── reminderagua.ico            # Ícono de la aplicación
├── remindermoto.py             # Entry point (logging + lanzar GUI)
├── remindermoto.spec           # Configuración PyInstaller
├── requirements.txt            # Dependencias Python
├── .gitignore
└── SDD.md                      # Este documento
```

---

## 4. Configuración (config.json)

```json
{
    "destinatarios": ["email1@example.com"],
    "asunto": "Reminder de Pagar la moto de [Mes Actual] de [año en numero]",
    "cuerpo": "Recordatorio de pagar los Q400 de la moto de [Mes Actual] de [año en numero]",
    "auto_close": true,
    "auto_close_delay": 60,
    "send_method": "outlook",
    "smtp": {
        "host": "smtp-mail.outlook.com",
        "port": 587,
        "email": "tu@hotmail.com",
        "password": "tu_contraseña_de_app"
    },
    "cuenta_outlook": "tu@hotmail.com",
    "idioma": "es"
}
```

---

## 5. Problema Hotmail - Solución

### Causa del error
`win32com` despacha Outlook mediante MAPI. Las cuentas Hotmail/Outlook.com con autenticación moderna (OAuth2) pueden fallar con `SendUsingAccount` si Outlook no está correctamente autenticado o si se ejecuta sin sesión de usuario activa.

### Solución v2.0
Modo **SMTP Directo**: usa `smtplib` con STARTTLS para conectarse a `smtp-mail.outlook.com:587`.

**Configuración para Hotmail:**
- Servidor: `smtp-mail.outlook.com`
- Puerto: `587`
- Email: `tu_cuenta@hotmail.com`
- Password: Contraseña de aplicación (si tienes 2FA) o contraseña normal

**Cómo activar:**
1. En la app, seleccionar "SMTP directo (Hotmail, Gmail, etc.)"
2. Ingresar correo y contraseña
3. Guardar configuración

---

## 6. Instrucciones de Compilación

```powershell
# Instalar dependencias
pip install -r requirements.txt
pip install pyinstaller

# Compilar dejando el .exe junto al .py principal
powershell -ExecutionPolicy Bypass -File .\build_remindermoto.ps1

# Alternativa manual equivalente
pyinstaller --noconfirm --distpath . --workpath build remindermoto.spec

# El ejecutable estará en:
# .\remindermoto.exe
```

La compilación oficial del proyecto deja `remindermoto.exe` en la raíz del repositorio,
junto a `remindermoto.py`. Esto mantiene alineadas la ruta del ejecutable, `config.json`
y `reminder.log`, que la app resuelve desde la carpeta del `.exe`.

En modo compilado, `config.json` se lee y se escribe exclusivamente desde la misma carpeta
que `remindermoto.exe`. El directorio de trabajo actual (`cwd`) no tiene prioridad sobre
la carpeta del ejecutable.

La app también migra en memoria configuraciones legadas al esquema actual para mantener
compatibilidad con archivos antiguos sin requerir edición manual del `config.json`.

---

## 7. Historial de Cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2025-02 | Versión inicial - Outlook only |
| 2.0 | 2026-06-19 | SMTP Hotmail, multi-idioma, threading, arquitectura modular, botón donación |
| 2.1 | 2026-06-20 | Reemplazo robusto de placeholders de mes/año |
| 2.2 | 2026-06-20 | Build oficial genera `remindermoto.exe` en la misma carpeta que `remindermoto.py` |
| 2.3 | 2026-06-20 | El `.exe` usa únicamente el `config.json` ubicado en su misma carpeta |
| 2.4 | 2026-06-20 | Compatibilidad automática con claves legadas de `config.json` |
