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

    # Procesamos el update dentro del loop de la app
    asyncio.run_coroutine_threadsafe(
        telegram_app.process_update(update),
        telegram_app._loop
    )
    return Response("OK", status=200)


# 4. Inicializar la app del bot y configurar webhook (UNA sola vez al arrancar)
async def setup_bot():
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(url=f"{URL}/{TOKEN}")
    print("✅ Webhook configurado en:", f"{URL}/{TOKEN}")
    # Creamos un loop persistente para procesar updates
    telegram_app._loop = asyncio.get_running_loop()
    # Dejamos la app corriendo indefinidamente
    await asyncio.Event().wait()


def run_bot():
    asyncio.run(setup_bot())


if __name__ == "__main__":
    # Arrancamos el bot en un hilo de fondo
    import threading
    threading.Thread(target=run_bot, daemon=True).start()

    # Flask corre en el hilo principal (Render lo necesita así)
    app.run(host="0.0.0.0", port=PORT)
