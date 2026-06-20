# -*- mode: python ; coding: utf-8 -*-
#
# remindermoto.spec — Configuración de PyInstaller para ReminderMailpagomoto.
#
# Compilar con:
#   pyinstaller remindermoto.spec
#
# El ejecutable resultante estará en:
#   dist/remindermoto.exe
#
# Notas:
#   - console=False: no muestra ventana de consola (modo GUI limpio)
#   - icon: usa reminderagua.ico de la carpeta raíz
#   - datas: incluye archivos i18n dentro del exe (accesibles via sys._MEIPASS)
#   - hiddenimports: win32com necesita imports explícitos para PyInstaller

import os

block_cipher = None

# Ruta base del proyecto (donde está este .spec)
project_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['remindermoto.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        # Archivos de traducción (i18n) empaquetados en el .exe
        (os.path.join('src', 'i18n', 'es.json'), os.path.join('src', 'i18n')),
        (os.path.join('src', 'i18n', 'en.json'), os.path.join('src', 'i18n')),
        # Ícono de la aplicación (accesible en tiempo de ejecución si se necesita)
        ('reminderagua.ico', '.'),
    ],
    hiddenimports=[
        'win32com',
        'win32com.client',
        'win32com.server',
        'pythoncom',
        'pywintypes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='remindermoto',        # Nombre del ejecutable (remindermoto.exe)
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                   # Comprimir con UPX para reducir tamaño
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,              # Sin ventana de consola (app de escritorio)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='reminderagua.ico',    # Ícono del ejecutable
)
