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

# 1. Flask para el health check de UptimeRobot
app = Flask(__name__)

@app.route("/")
def health_check():
    return "OK", 200

# 2. La aplicación del bot
telegram_app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Ya estoy funcionando 24/7.")

telegram_app.add_handler(CommandHandler("start", start))

# 3. Webhook: recibe los mensajes de Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, telegram_app.bot)
    
    # Procesamos el update de forma segura
    asyncio.run(telegram_app.process_update(update))
    return Response("OK", status=200)

# 4. Arrancar todo
if __name__ == "__main__":
    # Configuramos el webhook con Telegram antes de arrancar Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_app.bot.set_webhook(url=f"{URL}/{TOKEN}"))
    print("✅ Webhook configurado correctamente.")
    
    # Arrancamos Flask (Render necesita que corra en el hilo principal)
    app.run(host="0.0.0.0", port=PORT)
