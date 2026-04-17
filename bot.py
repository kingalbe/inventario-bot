import os
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("Falta la variable de entorno ANTHROPIC_API_KEY")

client = Anthropic(api_key=ANTHROPIC_API_KEY)
DB_FILE = "inventario.json"

def cargar_inventario():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_inventario(items):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def inventario_como_texto():
    items = cargar_inventario()
    if not items:
        return "El inventario esta vacio."
    lineas = []
    for i, item in enumerate(items, 1):
        lineas.append(f"{i}. {item['objeto']} ({item['categoria']}) -> {item['mueble']}, {item['lugar']} [{item['fecha']}]")
    return "\n".join(lineas)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "Hola! Soy tu asistente de inventario del hogar.\n\n"
        "Puedes:\n"
        "- Decirme donde guardas algo: He guardado las llaves en el cajon del salon\n"
        "- Preguntarme donde esta algo: Donde estan las llaves?\n"
        "- Ver todo el inventario: /inventario\n"
        "- Borrar un objeto: /borrar nombre_del_objeto\n"
        "- Ver esta ayuda: /ayuda"
    )
    await update.message.reply_text(msg)

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def ver_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = inventario_como_texto()
    await update.message.reply_text(f"Inventario actual:\n\n{texto}")

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Indica que quieres borrar. Ejemplo: /borrar llaves")
        return
    termino = " ".join(context.args).lower()
    items = cargar_inventario()
    nuevos = [i for i in items if termino not in i["objeto"].lower()]
    borrados = len(items) - len(nuevos)
    if borrados > 0:
        guardar_inventario(nuevos)
        await update.message.reply_text(f"He eliminado {borrados} objeto(s) que contenian '{termino}'.")
    else:
        await update.message.reply_text(f"No encontre ningun objeto con '{termino}' en el inventario.")

async def procesar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    inventario_actual = inventario_como_texto()

    system_prompt = (
        "Eres un asistente que gestiona el inventario de objetos de una casa. "
        "Detecta si el usuario esta GUARDANDO un objeto o PREGUNTANDO donde esta algo. "
        "Responde UNICAMENTE con JSON valido, sin texto adicional, sin markdown, sin comillas triples. "
        "Usa esta estructura exacta segun el caso:\n"
        '{"accion":"guardar","objeto":"...","categoria":"...","mueble":"...","lugar":"...","respuesta":"..."}\n'
        '{"accion":"buscar","respuesta":"..."}\n'
        '{"accion":"otro","respuesta":"..."}\n'
        "Categorias validas: Llaves, Documentos, Herramientas, Ropa, Electronica, Juguetes, Cocina, Medicamentos, Otro.\n"
        "El campo respuesta es un mensaje amigable en español para el usuario.\n\n"
        f"Inventario actual:\n{inventario_actual}"
    )

    raw = ""
    try:
        respuesta = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": texto}]
        )

        raw = respuesta.content[0].text.strip()
        logger.info(f"Claude respondio: {raw}")

        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else parts[0]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        if data.get("accion") == "guardar":
            items = cargar_inventario()
            nuevo = {
                "objeto": data.get("objeto", "Desconocido"),
                "categoria": data.get("categoria", "Otro"),
                "mueble": data.get("mueble", ""),
                "lugar": data.get("lugar", ""),
                "fecha": datetime.now().strftime("%d/%m/%Y")
            }
            items.append(nuevo)
            guardar_inventario(items)

        await update.message.reply_text(data.get("respuesta", "Entendido."))

    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError: {e} | raw: '{raw}'")
        await update.message.reply_text("No pude interpretar la respuesta. Intenta de nuevo.")
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}", exc_info=True)
        await update.message.reply_text(f"Error: {type(e).__name__}: {str(e)[:200]}")

def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("Falta la variable de entorno TELEGRAM_TOKEN")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("inventario", ver_inventario))
    app.add_handler(CommandHandler("borrar", borrar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_mensaje))

    logger.info("Bot arrancado...")
    app.run_polling()

if __name__ == "__main__":
    main()
