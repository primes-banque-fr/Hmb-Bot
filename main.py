import os
import uuid
import logging
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
    return "🤖 HMB AI BOT ONLINE ✅"

def run_web():

    port = int(os.environ.get("PORT", 10000))

    web_app.run(
        host="0.0.0.0",
        port=port
    )

def keep_alive():

    t = Thread(target=run_web)
    t.start()

# ==================================================
# MEMORY
# ==================================================

memory = {}
voice_mode = {}

# ==================================================
# SYSTEM PROMPT
# ==================================================

SYSTEM_PROMPT = """
Tu es HMB AI.

Créé par LeRoy HMB.

Tu es une intelligence artificielle ultra avancée, moderne, élégante et luxueuse.

Tu aides dans :
- intelligence artificielle
- programmation
- cybersécurité
- bots Telegram
- développement web
- Python
- HTML
- JavaScript
- design
- création d’images
- football
- actualités temps réel

Tu réponds toujours :

✅ avec des emojis adaptés
✅ avec un style moderne
✅ avec une présentation très organisée
✅ avec des réponses propres et élégantes
✅ avec une mise en page professionnelle
✅ avec un ton intelligent et premium
✅ avec des espaces et titres bien organisés

Tu dois souvent utiliser :
- ✨
- 🔥
- ⚡
- 🎯
- 🚀
- 🤖
- 💡
- 🛡️
- 🎨
- 📌

Quand tu expliques quelque chose :
- organise bien les informations
- utilise des listes propres
- mets des titres
- rends la réponse belle à lire

Quand l’utilisateur demande une information récente :
utilise internet temps réel.

Tu ne dois jamais dire :
"mes données s'arrêtent en 2023".
"""

# ==================================================
# START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = """
🤖 HMB AI ONLINE ✨

👑 Créateur :
LeRoy HMB

⚡ Fonctionnalités Premium :

✅ IA Ultra intelligente
✅ Internet temps réel
✅ Football live
✅ Génération image IA
✅ Réponses vocales
✅ Voix masculine premium
✅ Reconnaissance vocale
✅ Mémoire intelligente

📌 Commandes :

/start
/help
/reset
/image
/voice
/live

🚀 Envoie simplement un message.
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
/live équipe

🎤 Commandes vocales :

parle en voix
parle en texte

🎨 Exemple image :
/image lion cyberpunk bleu

⚽ Exemple football :
/live barcelona

🤖 Tu peux aussi parler normalement avec l’IA.
"""

    await update.message.reply_text(txt)

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
            "🎨 Génération image en cours..."
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
            voice="fr-FR-HenriNeural"
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
# FOOTBALL LIVE
# ==================================================

async def live(update: Update, context: ContextTypes.DEFAULT_TYPE):

    team = " ".join(context.args)

    if not team:

        await update.message.reply_text(
            "❌ Utilisation : /live barcelona"
        )

        return

    try:

        headers = {
            "x-apisports-key": FOOTBALL_API_KEY
        }

        url = "https://v3.football.api-sports.io/fixtures?live=all"

        r = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        data = r.json()

        fixtures = data.get("response", [])

        result = []

        for match in fixtures:

            home = match["teams"]["home"]["name"]
            away = match["teams"]["away"]["name"]

            if team.lower() in home.lower() or team.lower() in away.lower():

                goals_home = match["goals"]["home"]
                goals_away = match["goals"]["away"]

                minute = match["fixture"]["status"]["elapsed"]

                result.append(
                    f"⚽ {home} {goals_home} - {goals_away} {away}\n⏱ {minute} min"
                )

        if not result:

            await update.message.reply_text(
                "❌ Aucun match live trouvé."
            )

            return

        await update.message.reply_text(
            "\n\n".join(result)
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            f"❌ Erreur football : {e}"
        )

# ==================================================
# VOICE MESSAGE
# ==================================================

async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    ogg_file = f"{uuid.uuid4()}.ogg"
    wav_file = f"{uuid.uuid4()}.wav"

    try:

        file = await context.bot.get_file(
            update.message.voice.file_id
        )

        await file.download_to_drive(ogg_file)

        audio = AudioSegment.from_ogg(ogg_file)

        audio.export(wav_file, format="wav")

        recognizer = sr.Recognizer()

        with sr.AudioFile(wav_file) as source:

            audio_data = recognizer.record(source)

            text = recognizer.recognize_google(
                audio_data,
                language="fr-FR"
            )

        update.message.text = text

        await ai_chat(update, context)

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ Impossible de reconnaître la voix."
        )

    finally:

        if os.path.exists(ogg_file):
            os.remove(ogg_file)

        if os.path.exists(wav_file):
            os.remove(wav_file)

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

        r = requests.post(
            url,
            json=payload,
            timeout=60
        )

        data = r.json()

        results = data.get("results", [])

        text = ""

        for item in results:

            text += (
                f"{item.get('title')}\n"
                f"{item.get('content')}\n\n"
            )

        return text

    except Exception as e:

        logger.error(e)

        return ""

# ==================================================
# AI CHAT
# ==================================================

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    # ==========================================
    # VOICE MODE
    # ==========================================

    if "parle en voix" in text.lower():

        voice_mode[user_id] = True

        await update.message.reply_text(
            "🎤 Mode voix activé ✅"
        )

        return

    if "parle en texte" in text.lower():

        voice_mode[user_id] = False

        await update.message.reply_text(
            "💬 Mode texte activé ✅"
        )

        return

    # ==========================================
    # IMAGE AUTO
    # ==========================================

    image_keywords = [
        "image",
        "dessine",
        "dessin",
        "photo",
        "logo",
        "génère",
        "genere",
        "crée",
    ]

    if any(word in text.lower() for word in image_keywords):

        try:

            await update.message.reply_text(
                "🎨 Création image IA..."
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
    # INTERNET REALTIME
    # ==========================================

    realtime_keywords = [
        "actualité",
        "news",
        "2025",
        "2026",
        "football",
        "score",
        "liga",
        "premier league",
        "champions league",
    ]

    web_data = ""

    if any(word in text.lower() for word in realtime_keywords):

        web_data = tavily_search(text)

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
    ]

    if web_data:

        messages.append({
            "role": "system",
            "content": f"Informations récentes :\n{web_data}"
        })

    messages += memory[user_id][-10:]

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
        # VOICE RESPONSE
        # ==========================================

        if voice_mode.get(user_id, False):

            filename = f"{uuid.uuid4()}.mp3"

            communicate = edge_tts.Communicate(
                text=response,
                voice="fr-FR-HenriNeural"
            )

            await communicate.save(filename)

            with open(filename, "rb") as audio:

                await update.message.reply_voice(
                    voice=audio
                )

            if os.path.exists(filename):
                os.remove(filename)

        else:

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
app.add_handler(CommandHandler("live", live))

# VOICE MESSAGE

app.add_handler(
    MessageHandler(
        filters.VOICE,
        voice_message
    )
)

# AI CHAT

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        ai_chat
    )
)

# ERROR HANDLER

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
