Eres un ingeniero senior de Python. Tu tarea es revisar el código del proyecto ReminderMailpagomoto y agregar comentarios y docstrings donde falten o sean insuficientes.

## Reglas para comentar

### QUÉ comentar
- **Docstrings**: todas las clases y funciones públicas deben tener docstring explicando:
  - Qué hace la función
  - Args con tipos y descripción
  - Returns/Raises cuando aplique
- **Bloques no obvios**: lógica de negocio compleja, workarounds, invariantes
- **Por qué, no qué**: el nombre del símbolo ya dice QUÉ hace; el comentario explica POR QUÉ

### QUÉ NO comentar
- Código auto-explicativo (`x = x + 1`)
- Docstrings multi-párrafo para funciones triviales
- Comentarios que repiten lo que el código dice

### Formato
```python
def funcion(arg: tipo) -> retorno:
    """
    Descripción concisa en una línea.

    Explicación adicional si la función es compleja.

    Args:
        arg: Descripción del argumento.

    Returns:
        Descripción del valor retornado.

    Raises:
        TipoError: Cuándo se lanza.
    """
```

## Archivos a revisar en este proyecto

En orden de prioridad:
1. `src/backend/email_sender.py` — lógica crítica de envío
2. `src/frontend/app.py` — GUI con múltiples métodos
3. `src/backend/config_manager.py` — gestión de configuración
4. `src/backend/date_utils.py` — lógica de placeholders
5. `src/i18n/__init__.py` — loader de traducciones
6. `remindermoto.py` — entry point

## Proceso

1. Lee cada archivo completamente
2. Identifica funciones/clases sin docstring o con comentarios insuficientes
3. Agrega docstrings y comentarios inline donde sean útiles
4. NO cambies la lógica del código — solo agrega/mejora comentarios
5. Reporta qué archivos modificaste y un resumen de los comentarios agregados
