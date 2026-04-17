import os
import json
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Anthropic()
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
        return "El inventario está vacío."
    lineas = []
    for i, item in enumerate(items, 1):
        lineas.append(f"{i}. {item['objeto']} ({item['categoria']}) → {item['mueble']}, {item['lugar']} [{item['fecha']}]")
    return "\n".join(lineas)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "¡Hola! Soy tu asistente de inventario del hogar 🏠\n\n"
        "Puedes:\n"
        "• Decirme dónde guardas algo: *\"He guardado las llaves en el cajón del salón\"*\n"
        "• Preguntarme dónde está algo: *\"¿Dónde están las llaves?\"*\n"
        "• Ver todo el inventario: /inventario\n"
        "• Borrar un objeto: /borrar nombre_del_objeto\n"
        "• Ver esta ayuda: /ayuda"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def ver_inventario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = inventario_como_texto()
    await update.message.reply_text(f"📦 *Inventario actual:*\n\n{texto}", parse_mode="Markdown")

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Indica qué quieres borrar. Ejemplo: /borrar llaves")
        return
    termino = " ".join(context.args).lower()
    items = cargar_inventario()
    nuevos = [i for i in items if termino not in i["objeto"].lower()]
    borrados = len(items) - len(nuevos)
    if borrados > 0:
        guardar_inventario(nuevos)
        await update.message.reply_text(f"✅ He eliminado {borrados} objeto(s) que contenían '{termino}'.")
    else:
        await update.message.reply_text(f"No encontré ningún objeto con '{termino}' en el inventario.")

async def procesar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    inventario_actual = inventario_como_texto()

    system_prompt = """Eres un asistente que gestiona el inventario de objetos de una casa.

Tu trabajo es detectar si el usuario:
1. Está GUARDANDO un objeto (dice dónde pone algo)
2. Está PREGUNTANDO dónde está algo
3. Está haciendo otra cosa (saludo, etc.)

Responde SIEMPRE con JSON puro sin markdown con esta estructura:
{
  "accion": "guardar" | "buscar" | "otro",
  "objeto": "nombre del objeto (solo si accion=guardar)",
  "categoria": "una de: Llaves, Documentos, Herramientas, Ropa, Electrónica, Juguetes, Cocina, Medicamentos, Otro",
  "mueble": "mueble o zona de la casa (solo si accion=guardar)",
  "lugar": "ubicación exacta dentro del mueble (solo si accion=guardar)",
  "respuesta": "mensaje amigable para enviar al usuario en español"
}

Inventario actual:
""" + inventario_actual

    try:
        respuesta = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": texto}]
        )
        raw = respuesta.content[0].text.strip()
        data = json.loads(raw)

        if data["accion"] == "guardar":
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

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Hubo un error procesando tu mensaje. Inténtalo de nuevo.")

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
