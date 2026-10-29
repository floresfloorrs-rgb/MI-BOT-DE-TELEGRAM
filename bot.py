import os
import asyncio
import logging
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

# Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))

# 1. Flask para que UptimeRobot y Render vean que estamos vivos
app = Flask(__name__)

@app.route("/")
def health_check():
    return "OK", 200

def run_flask():
    # Render asigna el puerto en la variable PORT
    app.run(host="0.0.0.0", port=PORT)

# 2. Configuración del Bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Ya estoy funcionando 24/7.")

def run_bot():
    # Creamos un loop nuevo para este hilo
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Construimos la app
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    print("🤖 Bot iniciado y escuchando mensajes...")
    # Esto se queda escuchando a Telegram (Polling)
    application.run_polling()

# 3. Arrancar todo
if __name__ == "__main__":
    # Arrancamos Flask en un hilo secundario (para que no bloquee el bot)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Arrancamos el bot en el hilo principal
    run_bot()
