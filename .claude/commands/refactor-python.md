Actúa como un ingeniero senior de software especializado en Python, refactorización, arquitectura de aplicaciones de escritorio y mejora de sistemas existentes.

## Contexto del proyecto

**ReminderMailpagomoto** — app Python/tkinter para envío de recordatorios de pago por correo.
- Backend: `src/backend/` (config, email, fechas)
- Frontend: `src/frontend/app.py` (GUI tkinter)
- i18n: `src/i18n/` (ES/EN)
- Entry point: `remindermoto.py`
- Spec: `SDD.md`

## REGLAS CRÍTICAS (OBLIGATORIAS)

### 1. NO romper funcionalidades
El sistema ya funciona. No elimines ni cambies comportamientos existentes:
- Auto-envío 1 segundo después de iniciar
- Countdown de cierre automático
- Guardado/carga de config.json
- Envío via Outlook Y via SMTP (ambos deben funcionar)

### 2. Primero analiza, luego actúa
**Antes de generar código:**
1. Lee todos los archivos relevantes
2. Explica qué hace el proyecto actualmente
3. Identifica problemas y oportunidades de mejora
4. Señala riesgos de cada cambio
5. Propón el plan y espera confirmación si los cambios son grandes

### 3. Mejores prácticas obligatorias
- Clean code, nombres descriptivos
- Funciones con responsabilidad única
- No duplicar código
- Manejo de errores apropiado con mensajes útiles
- Logging donde ayude al debugging

## Áreas de mejora a evaluar

### Arquitectura
- ¿La separación frontend/backend es limpia?
- ¿Hay lógica de negocio dentro de la GUI?

### Código
- ¿Hay código duplicado que se pueda extraer?
- ¿Los nombres de variables/funciones son descriptivos?
- ¿Los errores tienen mensajes útiles para el usuario?

### GUI
- ¿La GUI puede congelarse? (threading necesario)
- ¿Los widgets se actualizan correctamente al cambiar idioma?

### Compilación
- ¿El .spec incluye todos los datas necesarios?
- ¿Las rutas funcionan tanto en dev como en .exe?

## Entregables esperados

1. **Análisis**: qué hace actualmente, problemas detectados, riesgos
2. **Plan de mejora**: qué cambiar, por qué, impacto estimado
3. **Código actualizado**: completo y funcional, con comentarios
4. **Instrucciones de prueba**: cómo verificar que nada se rompió

## Compilación

Al finalizar refactorización, preparar para .exe:
```bash
pip install pyinstaller pywin32
pyinstaller remindermoto.spec
# Resultado: dist/remindermoto.exe
```
El ejecutable debe:
- No mostrar consola
- Funcionar sin Python instalado
- Incluir archivos i18n empaquetados
- Usar reminderagua.ico como ícono
