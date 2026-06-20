Eres un experto en git y GitHub. Tu tarea es hacer commit de los cambios actuales y hacer push al repositorio de GitHub de la cuenta erickson558.

## Pasos a seguir

1. **Verificar estado**: ejecuta `git status` y `git diff --stat` para ver qué cambió
2. **Crear .gitignore** si no existe con los patrones: `build/`, `dist/`, `__pycache__/`, `*.pyc`, `*.log`, `.venv/`, `venv/`
3. **Inicializar git** si no es un repositorio (`git init`)
4. **Verificar remoto**: si no hay remoto, crear el repositorio en GitHub con `gh repo create`
5. **Staging selectivo**: agregar solo archivos relevantes del proyecto (NO: build/, dist/, *.pyc, __pycache__, *.log, *.exe)
6. **Commit descriptivo**: mensaje en español que explique QUÉ cambió y POR QUÉ
7. **Push**: `git push origin main` (o master según la rama)

## Archivos que SIEMPRE excluir del commit
- `build/` y `dist/` (compilados PyInstaller)
- `*.exe` (ejecutables)
- `*.log` (logs de ejecución)
- `__pycache__/` y `*.pyc` (bytecode Python)
- `.venv/` o `venv/` (entorno virtual)
- Contraseñas en config.json → si config.json tiene password SMTP, advertir al usuario

## Cuenta GitHub
- Usuario: **erickson558**
- Auth: `gh` CLI ya autenticado (gho_****)
- Scopes disponibles: repo, workflow, gist, read:org

## Ejemplo de flujo completo

```bash
git init                          # Si no es repo
git remote add origin https://github.com/erickson558/ReminderMailpagomoto.git
git add src/ remindermoto.py remindermoto.spec requirements.txt .gitignore SDD.md config.json
git commit -m "feat: agregar soporte SMTP para Hotmail y multi-idioma"
git push -u origin main
```

Ejecuta cada paso, muestra el output, y reporta el URL del repositorio al finalizar.
