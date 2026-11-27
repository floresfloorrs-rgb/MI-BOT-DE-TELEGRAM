import os
import asyncio
import logging
import threading
import random
import json
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
import telegram

# Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

PORT = int(os.environ.get("PORT", 10000))
ARCHIVO_MEMORIA = "memoria_links.json"

def obtener_configuracion_bots():
    bots = []
    for key in os.environ:
        if key.startswith("BOT_TOKEN_"):
            num = key.split("_")[-1]
            token = os.environ.get(f"BOT_TOKEN_{num}")
            links_str = os.environ.get(f"CHAT_LINKS_{num}", "")

            chat_links = {}
            if links_str.strip():
                pares = links_str.split(";;")
                for par in pares:
                    par = par.strip()
                    if not par:
                        continue
                    if "|" in par:
                        chat_id, mensaje = par.split("|", 1)
                        chat_links[chat_id.strip()] = mensaje.strip()
                    else:
                        logging.warning(f"[Bot {num}] Par mal formado (falta |): {par}")

            if token and chat_links:
                bots.append({"token": token, "chat_links": chat_links, "id": num})
    return bots

# --- SISTEMA DE MEMORIA PERSISTENTE ---
def cargar_memoria():
    if os.path.exists(ARCHIVO_MEMORIA):
        try:
            with open(ARCHIVO_MEMORIA, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error leyendo memoria: {e}")
    return {}

def guardar_memoria(memoria):
    try:
        with open(ARCHIVO_MEMORIA, "w") as f:
            json.dump(memoria, f)
    except Exception as e:
        logging.error(f"Error guardando memoria: {e}")
# --------------------------------------

app = Flask(__name__)

@app.route("/")
def health_check():
    return "OK", 200

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("... ")

# --- NUEVO COMANDO DE PRUEBA ---
async def test_borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_id = context.bot_data["bot_id"]
    memoria_global = context.bot_data["memoria_global"]
    chat_id = str(update.effective_chat.id)
    
    # Mensaje de confirmación
    msg_confirmacion = await update.message.reply_text("🧹 Iniciando prueba de limpieza profunda...")
    
    # Verificamos si hay mensajes guardados para este chat
    if bot_id in memoria_global and chat_id in memoria_global[bot_id]:
        ids_a_borrar = memoria_global[bot_id][chat_id].copy()
        borrados_exitosos = 0
        
        for msg_id in ids_a_borrar:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                borrados_exitosos += 1
                await asyncio.sleep(1) # Pequeña pausa para no saturar a Telegram
            except Exception as e:
                logging.warning(f"[Bot {bot_id}] Error borrando {msg_id}: {e}")
        
        # Limpiamos la memoria de este chat porque ya intentamos borrar todo
        memoria_global[bot_id][chat_id] = []
        guardar_memoria(memoria_global)
        
        # Editamos el mensaje de confirmación con el resultado
        await msg_confirmacion.edit_text(
            f"✅ Prueba terminada.\n"
            f"Se encontraron {len(ids_a_borrar)} mensajes en memoria.\n"
            f"Se borraron con éxito {borrados_exitosos}.\n"
            f"(Los demás probablemente ya habían sido borrados antes)."
        )
    else:
        await msg_confirmacion.edit_text("❌ No hay mensajes guardados en mi memoria para este grupo.")
# -------------------------------

async def enviar_y_borrar_mensaje(context: ContextTypes.DEFAULT_TYPE):
    bot_id = context.bot_data["bot_id"]
    chat_links = context.bot_data["chat_links"]
    memoria_global = context.bot_data["memoria_global"]

    logging.info(f"[Bot {bot_id}] Iniciando ronda para {len(chat_links)} grupos...")

    for chat_id, mensaje_texto in chat_links.items():
        
        # 1. LIMPIEZA PROFUNDA DE MENSAJES ANTIGUOS
        if chat_id in memoria_global.get(bot_id, {}):
            ids_a_borrar = memoria_global[bot_id][chat_id].copy()
            
            for msg_id in ids_a_borrar:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    logging.info(f"[Bot {bot_id}] Borrado exitoso msg {msg_id} en {chat_id}.")
                    memoria_global[bot_id][chat_id].remove(msg_id)
                except Exception as e:
                    if "message to delete not found" in str(e).lower() or "message_id_invalid" in str(e).lower():
                        memoria_global[bot_id][chat_id].remove(msg_id)
                    else:
                        logging.warning(f"[Bot {bot_id}] No se pudo borrar {msg_id} aún: {e}")
            
            guardar_memoria(memoria_global)

        await asyncio.sleep(random.uniform(2.0, 10.0))

        try:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(random.uniform(1.0, 3.0))
        except Exception:
            pass

        # 2. FORMATO ANTI-EMOJIS (Saltos de línea)
        texto_formateado = f"\n{mensaje_texto.strip()}\n"

        try:
            mensaje = await context.bot.send_message(
                chat_id=chat_id,
                text=texto_formateado,
                disable_web_page_preview=False
            )
            
            if bot_id not in memoria_global:
                memoria_global[bot_id] = {}
            if chat_id not in memoria_global[bot_id]:
                memoria_global[bot_id][chat_id] = []
                
            memoria_global[bot_id][chat_id].append(mensaje.message_id)
            guardar_memoria(memoria_global)
            
            logging.info(f"[Bot {bot_id}] Link enviado a {chat_id} (ID: {mensaje.message_id}).")
        except Exception as e:
            logging.error(f"[Bot {bot_id}] Error al enviar a {chat_id}: {e}")

        await asyncio.sleep(random.uniform(10.0, 20.0))

    logging.info(f"[Bot {bot_id}] Ronda finalizada. Reprogramando...")
    siguiente_ronda = random.uniform(600, 660)
    context.job_queue.run_once(enviar_y_borrar_mensaje, siguiente_ronda)


def iniciar_bot(config, memoria_compartida):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    token = config["token"]
    bot_id = config["id"]
    chat_links = config["chat_links"]

    application = ApplicationBuilder().token(token).build()

    application.bot_data["bot_id"] = bot_id
    application.bot_data["chat_links"] = chat_links
    application.bot_data["memoria_global"] = memoria_compartida

    # Registramos los comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("testborrar", test_borrar)) # <-- NUEVO COMANDO

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not isinstance(context.error, telegram.error.Conflict):
            logging.error(f"[Bot {bot_id}] Error inesperado: {context.error}")

    application.add_error_handler(error_handler)

    application.job_queue.run_once(enviar_y_borrar_mensaje, 10)

    print(f"🤖 Bot {bot_id} iniciado con {len(chat_links)} grupos asignados.")
    
    application.run_polling(drop_pending_updates=True, stop_signals=None)


if __name__ == "__main__":
    lista_bots = obtener_configuracion_bots()

    if not lista_bots:
        print("❌ ERROR: No se encontraron variables BOT_TOKEN_X y CHAT_LINKS_X válidas.")
    else:
        print(f"🚀 Iniciando {len(lista_bots)} bots en paralelo...")
        
        memoria_global = cargar_memoria()
        
        threading.Thread(target=run_flask, daemon=True).start()

        hilos_bots = []
        for config in lista_bots:
            hilo = threading.Thread(target=iniciar_bot, args=(config, memoria_global), daemon=True)
            hilo.start()
            hilos_bots.append(hilo)

        for hilo in hilos_bots:
            hilo.join()
