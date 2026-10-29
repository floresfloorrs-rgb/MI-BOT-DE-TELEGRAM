import os
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
CHAT_ID = os.environ.get("CHAT_ID") # NUEVO: Leemos el ID del grupo

# NUEVO: Variable global para guardar el ID del mensaje que enviamos
ultimo_mensaje_id = None 

# 1. Flask para que UptimeRobot y Render vean que estamos vivos
app = Flask(__name__)

@app.route("/")
def health_check():
    return "OK", 200

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# 2. Configuración del Bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Ya estoy funcionando 24/7.")

# NUEVO: Función que se ejecutará cada 10 minutos
async def enviar_y_borrar_mensaje(context: ContextTypes.DEFAULT_TYPE):
    global ultimo_mensaje_id
    
    # 1. Intentar borrar el mensaje anterior si existe
    if ultimo_mensaje_id:
        try:
            await context.bot.delete_message(chat_id=CHAT_ID, message_id=ultimo_mensaje_id)
            logging.info("Mensaje anterior borrado con éxito.")
        except Exception as e:
            logging.warning(f"No se pudo borrar el mensaje (quizás ya no existe): {e}")
    
    # 2. Enviar el nuevo mensaje
    try:
        mensaje = await context.bot.send_message(chat_id=CHAT_ID, text="mensaje de prueba")
        ultimo_mensaje_id = mensaje.message_id # Guardamos el ID del nuevo mensaje
        logging.info("Nuevo mensaje enviado con éxito.")
    except Exception as e:
        logging.error(f"Error al enviar el mensaje: {e}")

def run_bot():
    # Construimos la app
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    # NUEVO: Configuramos el temporizador (JobQueue)
    # interval=600 segundos (10 minutos). first=10 significa que empiece a los 10 segundos.
    job_queue = application.job_queue
    job_queue.run_repeating(enviar_y_borrar_mensaje, interval=600, first=10)
    
    print("🤖 Bot iniciado, escuchando mensajes y con temporizador activo...")
    # Esto se queda escuchando a Telegram (Polling)
    application.run_polling(drop_pending_updates=True)

# 3. Arrancar todo
if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: Falta la variable BOT_TOKEN")
    else:
        # Arrancamos Flask en un hilo secundario
        threading.Thread(target=run_flask, daemon=True).start()
        
        # Arrancamos el bot en el hilo principal
        run_bot()
