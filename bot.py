import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Leemos el token desde las variables de entorno (lo configuraremos en Render)
TOKEN = os.environ.get("BOT_TOKEN")

# Creamos una pequeña página web para que Render esté feliz
app = Flask(__name__)

@app.route("/")
def home():
    return "¡Bot encendido y funcionando!"

# Comando /start de Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu nuevo bot creado en Render. 🤖")

# Función para arrancar el servidor web
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def main():
    # Arrancamos el servidor web en un hilo separado
    threading.Thread(target=run_flask, daemon=True).start()

    # Arrancamos el bot de Telegram
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    print("Bot iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
