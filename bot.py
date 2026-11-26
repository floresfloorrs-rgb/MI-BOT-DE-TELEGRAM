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


def obtener_configuracion_bots():

    """

    Lee variables de entorno con formato:

      BOT_TOKEN_X  = token del bot

      CHAT_LINKS_X = id1|mensaje1;;id2|mensaje2;;...

    Devuelve una lista de diccionarios con token, id y un dict {chat_id: mensaje}.

    """

    bots = []

    for key in os.environ:

        if key.startswith("BOT_TOKEN_"):

            num = key.split("_")[-1]

            token = os.environ.get(f"BOT_TOKEN_{num}")

            links_str = os.environ.get(f"CHAT_LINKS_{num}", "")


            # Parsear los pares chat_id|mensaje separados por ;;

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

    chat_links = context.bot_data["chat_links"]          # dict: {chat_id: mensaje}

    ultimos_mensajes = context.bot_data["ultimos_mensajes"]


    logging.info(f"[Bot {bot_id}] Iniciando ronda para {len(chat_links)} grupos...")


    for chat_id, mensaje_texto in chat_links.items():

        # 1. Borrar el mensaje anterior de ese grupo (si existe)

        if chat_id in ultimos_mensajes:

            try:

                await context.bot.delete_message(

                    chat_id=chat_id,

                    message_id=ultimos_mensajes[chat_id]

                )

                logging.info(f"[Bot {bot_id}] Mensaje anterior borrado en {chat_id}.")

            except Exception:

                pass  # Si ya no existe o no se puede borrar, ignoramos


        # 2. Espera aleatoria de 2 a 10 segundos (para no ser robótico)

        await asyncio.sleep(random.uniform(2.0, 10.0))


        # 3. Simular que está escribiendo

        try:

            await context.bot.send_chat_action(chat_id=chat_id, action="typing")

            await asyncio.sleep(random.uniform(1.0, 3.0))

        except Exception:

            pass


        # 4. Enviar el mensaje/link ÚNICO de ese grupo

        try:

            mensaje = await context.bot.send_message(

                chat_id=chat_id,

                text=mensaje_texto,

                disable_web_page_preview=False  # True si no quieres vista previa del link

            )

            ultimos_mensajes[chat_id] = mensaje.message_id

            logging.info(f"[Bot {bot_id}] Link enviado a {chat_id}.")

        except Exception as e:

            logging.error(f"[Bot {bot_id}] Error al enviar a {chat_id}: {e}")


        # 5. Pausa entre grupos (10 a 20 segundos)

        await asyncio.sleep(random.uniform(10.0, 20.0))


    logging.info(f"[Bot {bot_id}] Ronda finalizada. Reprogramando...")


    # 6. Próxima ronda en un tiempo variable entre 10 y 11 minutos

    siguiente_ronda = random.uniform(600, 660)

    context.job_queue.run_once(enviar_y_borrar_mensaje, siguiente_ronda)


def iniciar_bot(config):

    token = config["token"]

    bot_id = config["id"]

    chat_links = config["chat_links"]


    application = ApplicationBuilder().token(token).build()


    application.bot_data["bot_id"] = bot_id

    application.bot_data["chat_links"] = chat_links

    application.bot_data["ultimos_mensajes"] = {}


    application.add_handler(CommandHandler("start", start))


    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:

        if not isinstance(context.error, telegram.error.Conflict):

            logging.error(f"[Bot {bot_id}] Error inesperado: {context.error}")


    application.add_error_handler(error_handler)


    # Primera ejecución a los 10 segundos de arrancar

    application.job_queue.run_once(enviar_y_borrar_mensaje, 10)


    print(f"🤖 Bot {bot_id} iniciado con {len(chat_links)} grupos asignados.")

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":

    lista_bots = obtener_configuracion_bots()


    if not lista_bots:

        print("ERROR: No se encontraron variables BOT_TOKEN_X y CHAT_LINKS_X válidas.")

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
        
