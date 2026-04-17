# Bot de Telegram — Inventario del Hogar

Gestiona dónde guardas las cosas de tu casa desde Telegram con IA.

## Comandos del bot

| Comando | Qué hace |
|---|---|
| `/start` o `/ayuda` | Muestra la ayuda |
| `/inventario` | Lista todos los objetos guardados |
| `/borrar llaves` | Elimina un objeto por nombre |
| Texto libre | El bot detecta si estás guardando o buscando algo |

## Ejemplos de uso

- "He guardado las llaves del trastero en la caja del primer cajón del mueble del salón"
- "¿Dónde están mis llaves?"
- "Puse el pasaporte en el cajón izquierdo del armario del dormitorio"

## Despliegue en Railway (sin código)

### Paso 1 — Sube los archivos a GitHub
1. Ve a github.com y crea una cuenta gratuita si no tienes
2. Crea un repositorio nuevo (botón verde "New")
3. Sube estos 4 archivos: bot.py, requirements.txt, Procfile, railway.toml

### Paso 2 — Conecta Railway
1. Ve a railway.app e inicia sesión con tu cuenta de GitHub
2. Pulsa "New Project" → "Deploy from GitHub repo"
3. Selecciona el repositorio que acabas de crear

### Paso 3 — Añade las variables de entorno
En Railway, ve a tu proyecto → pestaña "Variables" y añade:

```
TELEGRAM_TOKEN = (el token que te dio BotFather)
ANTHROPIC_API_KEY = (tu clave de console.anthropic.com)
```

### Paso 4 — Despliega
Railway detectará el Procfile automáticamente y arrancará el bot.
En 1-2 minutos estará activo en Telegram.

## Variables de entorno necesarias

| Variable | Dónde obtenerla |
|---|---|
| `TELEGRAM_TOKEN` | @BotFather en Telegram → /newbot |
| `ANTHROPIC_API_KEY` | console.anthropic.com/keys |
