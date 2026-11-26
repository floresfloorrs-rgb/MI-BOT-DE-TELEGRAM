import os

import asyncio

import logging

import threading

import random

from flask import Flask

from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from telegram import Update

import telegram


logging.basicConfig(

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',

    level=logging.INFO

)


PORT = int(os.environ.get("PORT", 10000))


# Lista de mensajes con emojis al inicio y al final

MENSAJES_VARIADOS = [

    "📢 📌 Mensaje de prueba 📌 📢",

    "👋 ℹ️ ¡Hola a todos! Mensaje de prueba ℹ️ 👋",

    "📝 ✅ Aviso: mensaje de prueba ✅ 📝",

    "⏰ 🔄 Recordatorio: mensaje de prueba 🔄 ⏰",

    "📅 📢 Mensaje de prueba (actualizado) 📢 📅"

]


def obtener_configuracion_bots():

    bots = []

    for key in os.environ:

        if key.startswith("BOT_TOKEN_"):

            num = key.split("_")[-1]

            token = os.environ.get(f"BOT_TOKEN_{num}")

            chat_ids_str = os.environ.get(f"CHAT_IDS_{num}", "")

            chat_ids = [c.strip() for c in chat_ids_str.split(",") if c.strip()]

            

            if token and chat_ids:

                bots.append({"token": token, "chat_ids": chat_ids, "id": num})

    return bots


app = Flask(__name__)


@app.route("/")

def health_check():

    return "OK", 200


def run_flask():

    app.run(host="0.0.0.0", port=PORT)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("¡Hola! Ya estoy funcionando 24/7.")


async def enviar_y_borrar_mensaje(context: ContextTypes.DEFAULT_TYPE):

    bot_id = context.bot_data["bot_id"]

    chat_ids = context.bot_data["chat_ids"]

    ultimos_mensajes = context.bot_data["ultimos_mensajes"]

    

    logging.info(f"[Bot {bot_id}] Iniciando ronda para {len(chat_ids)} grupos...")


    for chat_id in chat_ids:

        # 1. Borrar mensaje anterior

        if chat_id in ultimos_mensajes:

            try:

                await context.bot.delete_message(chat_id=chat_id, message_id=ultimos_mensajes[chat_id])

                logging.info(f"[Bot {bot_id}] Mensaje borrado en {chat_id}.")

            except Exception:

                pass

        

        # 2. Espera aleatoria de 2 a 10 segundos

        espera_borrado = random.uniform(2.0, 10.0)

        await asyncio.sleep(espera_borrado)

        

        # 3. Simular escritura (Typing)

        try:

            await context.bot.send_chat_action(chat_id=chat_id, action="typing")

            await asyncio.sleep(random.uniform(1.0, 3.0))

        except Exception:

             pass


        # 4. Enviar el nuevo mensaje

        try:

            texto = random.choice(MENSAJES_VARIADOS)

            mensaje = await context.bot.send_message(chat_id=chat_id, text=texto)

            ultimos_mensajes[chat_id] = mensaje.message_id

            logging.info(f"[Bot {bot_id}] Mensaje enviado a {chat_id}.")

        except Exception as e:

            logging.error(f"[Bot {bot_id}] Error al enviar a {chat_id}: {e}")

        

        # 5. Pausa entre grupos (10 a 20 segundos)

        espera_siguiente = random.uniform(10.0, 20.0)

        await asyncio.sleep(espera_siguiente)


    logging.info(f"[Bot {bot_id}] Ronda finalizada. Esperando para la siguiente...")

    

    # 6. Reprogramar la siguiente ronda variando el tiempo (10 a 11 minutos)

    siguiente_ronda = random.uniform(600, 660) 

    context.job_queue.run_once(enviar_y_borrar_mensaje, siguiente_ronda)


def iniciar_bot(config):

    token = config["token"]

    bot_id = config["id"]

    chat_ids = config["chat_ids"]

    

    # NUEVO: Crear un nuevo event loop para este hilo específico (Soluciona el error de Render)

    loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)

    

    application = ApplicationBuilder().token(token).build()

    

    application.bot_data["bot_id"] = bot_id

    application.bot_data["chat_ids"] = chat_ids

    application.bot_data["ultimos_mensajes"] = {}

    

    application.add_handler(CommandHandler("start", start))

    

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:

        if not isinstance(context.error, telegram.error.Conflict):

            logging.error(f"[Bot {bot_id}] Error inesperado: {context.error}")


    application.add_error_handler(error_handler)

    

    # Primera ejecución a los 10 segundos de arrancar

    application.job_queue.run_once(enviar_y_borrar_mensaje, 10)

    

    print(f"🤖 Bot {bot_id} iniciado con {len(chat_ids)} grupos asignados.")

    

    # Arrancamos el bot

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":

    lista_bots = obtener_configuracion_bots()

    

    if not lista_bots:

        print("ERROR: No se encontraron variables BOT_TOKEN_X y CHAT_IDS_X en el entorno.")

    else:

        print(f"🚀 Iniciando {len(lista_bots)} bots en paralelo...")

        threading.Thread(target=run_flask, daemon=True).start()

        

        hilos_bots = []

        for config in lista_bots:

            hilo = threading.Thread(target=iniciar_bot, args=(config,), daemon=True)

            hilo.start()

            hilos_bots.append(hilo)

        

        for hilo in hilos_bots:

            hilo.join()
