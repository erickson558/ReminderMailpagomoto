Eres un experto en PyInstaller y distribución de aplicaciones Python para Windows. Tu tarea es compilar ReminderMailpagomoto a un ejecutable .exe standalone.

## Requisitos previos

Verificar que estén instalados:
```bash
pip install pyinstaller pywin32
```

## Proceso de compilación

### 1. Limpiar build anterior
```bash
# Eliminar carpetas de build previo para compilación limpia
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
```

### 2. Compilar con el spec
```bash
pyinstaller remindermoto.spec
```

### 3. Verificar resultado
El ejecutable estará en: `dist/remindermoto.exe`

Verificar que:
- El archivo existe y tiene tamaño razonable (10-30 MB)
- Al ejecutar: no aparece ventana de consola
- La GUI se muestra correctamente
- Los archivos i18n funcionan (probar cambio de idioma)
- El ícono reminderagua.ico aparece en la barra de tareas

## Qué incluye el spec actual

- `console=False` → sin ventana de consola
- `icon='reminderagua.ico'` → ícono del exe
- `datas`: archivos i18n (es.json, en.json) y el .ico
- `hiddenimports`: win32com, pythoncom (necesarios para Outlook)
- UPX compresión habilitada

## Solución de problemas comunes

### Error: "win32com not found"
```bash
pip install pywin32
python -m pywin32_postinstall -install
```

### Error: "i18n files not found" al ejecutar el .exe
Verificar que el .spec tiene:
```python
datas=[
    ('src/i18n/es.json', 'src/i18n'),
    ('src/i18n/en.json', 'src/i18n'),
]
```

### Ejecutable demasiado grande
Agregar al .spec:
```python
excludes=['matplotlib', 'numpy', 'pandas', 'PIL', 'scipy'],
```

### La app no encuentra config.json
El exe busca config.json en `os.path.dirname(sys.executable)` — debe estar en la misma carpeta que el .exe.

## Post-compilación

Después de compilar exitosamente:
1. Probar `dist/remindermoto.exe` manualmente
2. Hacer commit de cambios en .spec si hubo modificaciones
3. Usar `/github-push` para subir a GitHub
4. Si se actualizó el Task Scheduler, actualizar también la ruta en la tarea programada

## Notas importantes

- El .exe en `dist/` NO se sube al repositorio GitHub (está en .gitignore)
- `reminder.log` se crea en la misma carpeta que el .exe al ejecutar
- Para actualizar la app en producción: recompilar y reemplazar el .exe
