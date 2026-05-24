import os
import uuid
import logging
import asyncio
import requests
import edge_tts
import speech_recognition as sr

from flask import Flask
from threading import Thread

from dotenv import load_dotenv
from pydub import AudioSegment

from telegram import Update
from telegram.constants import ChatAction

from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# ==================================================
# LOAD ENV
# ==================================================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# ==================================================
# FLASK KEEP ALIVE
# ==================================================

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "HMB AI BOT ONLINE ✅"

def run_web():

    port = int(os.environ.get("PORT", 10000))

    web_app.run(
        host="0.0.0.0",
        port=port
    )

def keep_alive():

    t = Thread(target=run_web)

    t.daemon = True

    t.start()

# ==================================================
# MEMORY
# ==================================================

memory = {}

# ==================================================
# SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """
Tu es HMB AI.

Créé par LeRoy HMB.

Tu es une intelligence artificielle extrêmement avancée.

Tu aides dans :
- programmation
- cybersécurité
- bots Telegram
- intelligence artificielle
- développement
- Python
- HTML
- JavaScript
- design
- création d’images
- hacking éthique

Tu réponds toujours de manière :
- intelligente
- rapide
- professionnelle
- moderne

Tu peux répondre aux actualités récentes.
Tu peux discuter du football actuel.
Tu peux parler des nouvelles technologies.
"""

# ==================================================
# START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = """
🤖 HMB AI ONLINE

👑 Créateur :
LeRoy HMB

⚡ IA ultra intelligente activée

📌 Commandes :

/help
/reset
/image
/voice

🎤 Envoie aussi des messages vocaux.

💬 Envoie simplement un message.
"""

    await update.message.reply_text(txt)

# ==================================================
# HELP
# ==================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = """
📌 COMMANDES DISPONIBLES

/start
/help
/reset
/image prompt
/voice texte

🎨 Exemple :
/image lion cyberpunk

🎤 Exemple :
/voice Bonjour bienvenue

🎙️ Tu peux aussi envoyer un vocal directement.
"""

    await update.message.reply_text(txt)

# ==================================================
# RESET MEMORY
# ==================================================

async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    memory[user_id] = []

    await update.message.reply_text(
        "🧠 Mémoire supprimée."
    )

# ==================================================
# AI RESPONSE
# ==================================================

async def generate_ai_response(user_id, text):

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append({
        "role": "user",
        "content": text
    })

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ] + memory[user_id][-10:]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://openrouter.ai",
        "X-Title": "HMB AI"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1200
    }

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=90
    )

    data = r.json()

    if "choices" not in data:
        return f"❌ Erreur API : {data}"

    response = data["choices"][0]["message"]["content"]

    memory[user_id].append({
        "role": "assistant",
        "content": response
    })

    if len(memory[user_id]) > 20:
        memory[user_id] = memory[user_id][-20:]

    return response

# ==================================================
# IMAGE GENERATION
# ==================================================

async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):

    prompt = " ".join(context.args)

    if not prompt:

        await update.message.reply_text(
            "❌ Utilisation : /image voiture futuriste"
        )

        return

    try:

        await update.message.reply_text(
            "🎨 Génération de l'image..."
        )

        image_url = (
            f"https://image.pollinations.ai/prompt/"
            f"{prompt}?width=1024&height=1024&model=flux"
        )

        await update.message.reply_photo(
            photo=image_url
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            f"❌ Erreur image : {e}"
        )

# ==================================================
# VOICE GENERATION
# ==================================================

async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = " ".join(context.args)

    if not text:

        await update.message.reply_text(
            "❌ Utilisation : /voice Bonjour"
        )

        return

    filename = f"{uuid.uuid4()}.mp3"

    try:

        await update.message.chat.send_action(
            action=ChatAction.RECORD_VOICE
        )

        communicate = edge_tts.Communicate(
            text=text,
            voice="fr-FR-RemyMultilingualNeural"
        )

        await communicate.save(filename)

        with open(filename, "rb") as audio:

            await update.message.reply_voice(
                voice=audio
            )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            f"❌ Erreur voice : {e}"
        )

    finally:

        if os.path.exists(filename):
            os.remove(filename)

# ==================================================
# VOICE MESSAGE
# ==================================================

async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        await update.message.reply_text(
            "🎙️ Analyse du vocal..."
        )

        voice = await update.message.voice.get_file()

        ogg_file = f"{uuid.uuid4()}.ogg"
        wav_file = f"{uuid.uuid4()}.wav"
        mp3_file = f"{uuid.uuid4()}.mp3"

        await voice.download_to_drive(ogg_file)

        audio = AudioSegment.from_ogg(ogg_file)

        audio.export(wav_file, format="wav")

        recognizer = sr.Recognizer()

        with sr.AudioFile(wav_file) as source:

            audio_data = recognizer.record(source)

            text = recognizer.recognize_google(
                audio_data,
                language="fr-FR"
            )

        await update.message.reply_text(
            f"🗣️ Tu as dit : {text}"
        )

        response = await generate_ai_response(
            update.effective_user.id,
            text
        )

        await update.message.reply_text(response)

        communicate = edge_tts.Communicate(
            text=response,
            voice="fr-FR-RemyMultilingualNeural"
        )

        await communicate.save(mp3_file)

        with open(mp3_file, "rb") as audio_file:

            await update.message.reply_voice(
                voice=audio_file
            )

        # DELETE FILES

        for file in [ogg_file, wav_file, mp3_file]:

            if os.path.exists(file):
                os.remove(file)

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            f"❌ Erreur vocal : {e}"
        )

# ==================================================
# AI CHAT
# ==================================================

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    image_keywords = [
        "image",
        "dessine",
        "dessin",
        "photo",
        "génère",
        "genere",
        "crée",
        "cree",
        "logo",
    ]

    if any(word in text.lower() for word in image_keywords):

        try:

            await update.message.reply_text(
                "🎨 Création de l'image..."
            )

            image_url = (
                f"https://image.pollinations.ai/prompt/"
                f"{text}?width=1024&height=1024&model=flux"
            )

            await update.message.reply_photo(
                photo=image_url
            )

            return

        except Exception as e:

            logger.error(e)

            await update.message.reply_text(
                f"❌ Erreur image : {e}"
            )

            return

    try:

        await update.message.chat.send_action(
            action=ChatAction.TYPING
        )

        response = await generate_ai_response(
            user_id,
            text
        )

        if len(response) > 4000:
            response = response[:4000]

        await update.message.reply_text(response)

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            f"❌ Erreur IA : {e}"
        )

# ==================================================
# ERROR HANDLER
# ==================================================

async def error_handler(update, context):

    logger.error(
        msg="Exception while handling update:",
        exc_info=context.error
    )

# ==================================================
# MAIN
# ==================================================

async def main():

    app = ApplicationBuilder().token(TOKEN).build()

    # COMMANDS

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset_memory))
    app.add_handler(CommandHandler("image", image))
    app.add_handler(CommandHandler("voice", voice))

    # VOICE MESSAGE

    app.add_handler(
        MessageHandler(
            filters.VOICE,
            voice_message
        )
    )

    # TEXT CHAT

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            ai_chat
        )
    )

    # ERROR

    app.add_error_handler(error_handler)

    print("🤖 HMB AI ONLINE ✅")

    keep_alive()

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

# ==================================================
# START BOT
# ==================================================

if __name__ == "__main__":

    asyncio.run(main())
