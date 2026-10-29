import os
import threading
from flask import Flask
# ... tus imports del bot (telegram, etc.)

# ====== TU CÓDIGO DEL BOT EXISTENTE VA AQUÍ ARRIBA ======
# (no lo toques, déjalo como estaba)


# ====== SERVIDOR WEB PARA UPTIMEROBOT ======
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot activo", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ====== INICIAR AMBOS ======
if __name__ == "__main__":
    # Iniciar servidor web en un hilo aparte
    threading.Thread(target=run_web, daemon=True).start()
    
    # Iniciar tu bot (polling) - esto depende de tu librería
    # Ejemplo con python-telegram-bot v20+:
    # application.run_polling()
    
    # Ejemplo con pyTelegramBotAPI:
    # bot.infinity_polling()
