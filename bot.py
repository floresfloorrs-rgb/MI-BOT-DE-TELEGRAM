import os
import asyncio
import logging
from flask import Flask, request, Response
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuración de logs para ver la actividad en Render
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")
URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 10000))

# 1. Creamos la aplicación de Flask para el chequeo de salud
app = Flask(__name__)

@app.route("/")
def health_check():
    return "OK", 200

# 2. Creamos la aplicación del bot de Telegram
telegram_app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Ya estoy funcionando 24/7.")

telegram_app.add_handler(CommandHandler("start", start))

# 3. Ruta que recibirá los mensajes de Telegram (Webhook)
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.run(telegram_app.process_update(update))
    return Response("OK", status=200)

# 4. Función principal que inicia todo
async def main():
    # Configuramos el webhook de Telegram
    await telegram_app.bot.set_webhook(url=f"{URL}/{TOKEN}")
    print("Webhook configurado correctamente.")
    
    # Iniciamos Flask
    app.run(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    asyncio.run(main())
