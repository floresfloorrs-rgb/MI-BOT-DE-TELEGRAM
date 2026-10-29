import os
import asyncio
import logging
from flask import Flask, request, Response
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("BOT_TOKEN")
URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", 10000))

# 1. Flask
app = Flask(__name__)

@app.route("/")
def health_check():
    return "OK", 200

# 2. App del Bot
telegram_app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Ya estoy funcionando 24/7.")

telegram_app.add_handler(CommandHandler("start", start))

# 3. Ruta del Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    
    # Ejecutamos esto en el loop que creamos abajo (SIN asyncio.run)
    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        background_loop
    )
    return Response("OK", status=200)

# 4. Arrancar
if __name__ == "__main__":
    # Creamos un loop global que corra siempre en segundo plano
    background_loop = asyncio.new_event_loop()
    
    async def setup():
        await telegram_app.initialize()
        await telegram_app.bot.set_webhook(url=f"{URL}/{TOKEN}")
        print("✅ Webhook configurado correctamente.")

    background_loop.run_until_complete(setup())
    
    # Encendemos Flask
    app.run(host="0.0.0.0", port=PORT)
