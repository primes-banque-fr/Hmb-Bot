import os
import uuid
import logging
import requests
import edge_tts
import speech_recognition as sr
import subprocess

from flask import Flask
from threading import Thread
from dotenv import load_dotenv

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
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")

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
    return "🤖 HMB AI ONLINE ✅"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ==================================================
# MEMORY
# ==================================================

memory = {}

# ==================================================
# SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """
Tu es HMB AI 👑

Créé par LeRoy HMB.

Tu es une IA ultra intelligente, moderne et luxueuse.

Tu réponds toujours de manière :
- élégante
- organisée
- professionnelle
- moderne
- luxueuse
- intelligente

Tu utilises souvent :
✨ 🚀 🔥 ⚡ 💎 🤖

Tu aides dans :
- programmation
- Python
- bots Telegram
- cybersécurité
- intelligence artificielle
- football live
- actualités temps réel
- création d’images
- développement web
- design
- hacking éthique

Quand quelqu’un demande une réponse vocale,
tu réponds automatiquement avec une voix masculine puissante.
"""

# ==================================================
# START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
🤖 HMB AI ONLINE ✅

👑 Créateur : LeRoy HMB

⚡ IA Ultra Intelligente Activée

✨ Fonctionnalités :
• IA avancée
• Internet temps réel
• Football live
• Génération image
• Réponse vocale
• Reconnaissance vocale

📌 Commandes :

/start
/help
/reset
/image
/voice
/live

💬 Parle simplement avec le bot.
"""

    await update.message.reply_text(text)

# ==================================================
# HELP
# ==================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
📌 COMMANDES DISPONIBLES

/start
/help
/reset
/image prompt
/voice texte
/live

🎨 Exemple :
/image voiture futuriste bleue

🎤 Exemple :
/voice Bonjour bienvenue

⚽ Exemple :
/live

🌐 Tu peux aussi demander :
- actualités
- scores football
- météo
- informations récentes
"""

    await update.message.reply_text(text)

# ==================================================
# RESET MEMORY
# ==================================================

async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    memory[user_id] = []

    await update.message.reply_text(
        "🧠 Mémoire supprimée avec succès ✅"
    )

# ==================================================
# INTERNET SEARCH
# ==================================================

def tavily_search(query):

    try:

        url = "https://api.tavily.com/search"

        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5
        }

        r = requests.post(url, json=payload, timeout=30)

        data = r.json()

        if "results" not in data:
            return None

        results = data["results"]

        text = "🌐 Résultats Internet Temps Réel :\n\n"

        for item in results[:3]:

            text += f"🔹 {item['title']}\n"
            text += f"{item['content'][:200]}...\n\n"

        return text

    except Exception as e:
        logger.error(e)
        return None

# ==================================================
# FOOTBALL LIVE
# ==================================================

async def live_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        url = "https://v3.football.api-sports.io/fixtures?live=all"

        headers = {
            "x-apisports-key": FOOTBALL_API_KEY
        }

        r = requests.get(url, headers=headers, timeout=30)

        data = r.json()

        matches = data.get("response", [])

        if not matches:

            await update.message.reply_text(
                "⚽ Aucun match live actuellement."
            )

            return

        text = "⚽ MATCHS EN DIRECT 🔥\n\n"

        for match in matches[:10]:

            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]

            home_goals = match["goals"]["home"]
            away_goals = match["goals"]["away"]

            minute = match["fixture"]["status"]["elapsed"]

            text += (
                f"🏟 {home} {home_goals} - {away_goals} {away}\n"
                f"⏱ {minute} min\n\n"
            )

        await update.message.reply_text(text)

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            f"❌ Erreur football : {e}"
        )

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
            "🎨 Génération de l'image en cours..."
        )

        image_url = (
            f"https://image.pollinations.ai/prompt/"
            f"{prompt}?width=1024&height=1024&model=flux"
        )

        await update.message.reply_photo(photo=image_url)

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            f"❌ Erreur image : {e}"
        )

# ==================================================
# VOICE GENERATION
# ==================================================

async def generate_voice(text):

    mp3_file = f"{uuid.uuid4()}.mp3"

    communicate = edge_tts.Communicate(
        text,
        voice="fr-FR-HenriNeural"
    )

    await communicate.save(mp3_file)

    return mp3_file

# ==================================================
# VOICE COMMAND
# ==================================================

async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = " ".join(context.args)

    if not text:

        await update.message.reply_text(
            "❌ Utilisation : /voice Bonjour"
        )

        return

    try:

        await update.message.chat.send_action(
            action=ChatAction.RECORD_VOICE
        )

        audio_file = await generate_voice(text)

        with open(audio_file, "rb") as audio:

            await update.message.reply_voice(audio)

        os.remove(audio_file)

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            f"❌ Erreur voice : {e}"
        )

# ==================================================
# VOICE MESSAGE RECOGNITION
# ==================================================

async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        file = await context.bot.get_file(
            update.message.voice.file_id
        )

        ogg_file = f"{uuid.uuid4()}.ogg"
        wav_file = f"{uuid.uuid4()}.wav"

        await file.download_to_drive(ogg_file)

        subprocess.run([
            "ffmpeg",
            "-i",
            ogg_file,
            wav_file
        ])

        recognizer = sr.Recognizer()

        with sr.AudioFile(wav_file) as source:

            audio = recognizer.record(source)

        text = recognizer.recognize_google(
            audio,
            language="fr-FR"
        )

        await update.message.reply_text(
            f"🎤 Tu as dit :\n\n{text}"
        )

        fake_update = update
        fake_update.message.text = text

        await ai_chat(fake_update, context)

        os.remove(ogg_file)
        os.remove(wav_file)

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ Impossible de reconnaître la voix."
        )

# ==================================================
# AI CHAT
# ==================================================

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text.lower()

    # ==========================================
    # FOOTBALL LIVE AUTO
    # ==========================================

    football_keywords = [
        "match",
        "football",
        "score",
        "live",
        "liga",
        "premier league"
    ]

    if any(word in text for word in football_keywords):

        await live_scores(update, context)
        return

    # ==========================================
    # INTERNET REALTIME
    # ==========================================

    realtime_keywords = [
        "actualité",
        "news",
        "récent",
        "aujourd'hui",
        "internet"
    ]

    if any(word in text for word in realtime_keywords):

        result = tavily_search(text)

        if result:

            await update.message.reply_text(result)
            return

    # ==========================================
    # AUTO IMAGE
    # ==========================================

    image_keywords = [
        "image",
        "dessine",
        "logo",
        "photo",
        "crée",
        "génère"
    ]

    if any(word in text for word in image_keywords):

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

    # ==========================================
    # MEMORY
    # ==========================================

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
        "temperature": 0.8,
        "max_tokens": 1500
    }

    try:

        await update.message.chat.send_action(
            action=ChatAction.TYPING
        )

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
        )

        data = r.json()

        if "choices" not in data:

            await update.message.reply_text(
                f"❌ Réponse API invalide : {data}"
            )

            return

        response = data["choices"][0]["message"]["content"]

        memory[user_id].append({
            "role": "assistant",
            "content": response
        })

        if len(memory[user_id]) > 20:
            memory[user_id] = memory[user_id][-20:]

        if len(response) > 4000:
            response = response[:4000]

        # ==========================================
        # AUTO VOICE
        # ==========================================

        voice_keywords = [
            "parle",
            "voix",
            "audio",
            "dis-le"
        ]

        if any(word in text for word in voice_keywords):

            audio_file = await generate_voice(response)

            with open(audio_file, "rb") as audio:

                await update.message.reply_voice(audio)

            os.remove(audio_file)

            return

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
# MAIN APP
# ==================================================

app = ApplicationBuilder().token(TOKEN).build()

# COMMANDS

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("reset", reset_memory))
app.add_handler(CommandHandler("image", image))
app.add_handler(CommandHandler("voice", voice))
app.add_handler(CommandHandler("live", live_scores))

# CHAT

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        ai_chat
    )
)

# VOICE

app.add_handler(
    MessageHandler(
        filters.VOICE,
        voice_message
    )
)

# ERROR

app.add_error_handler(error_handler)

# ==================================================
# START BOT
# ==================================================

if __name__ == "__main__":

    print("🤖 HMB AI ONLINE ✅")

    keep_alive()

    app.run_polling(
        drop_pending_updates=True
)
