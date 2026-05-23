import os
import requests
from gtts import gTTS
from dotenv import load_dotenv
from supabase import create_client

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER = os.getenv("OPENROUTER_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")
OWNER_ID = int(os.getenv("OWNER_ID"))

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

memory = {}

SYSTEM_PROMPT = """
Tu es HMB AI.

Créé par LeRoy HMB.

Tu es extrêmement intelligent.

Tu aides dans :
- programmation
- cybersécurité
- bots Telegram
- intelligence artificielle
- développement
- design
- création d’images
- code Python
- HTML
- JavaScript
- hacking éthique

Tu réponds de manière professionnelle.
"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    try:
        supabase.table("users").upsert({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }).execute()
    except Exception:
        pass

    txt = f"""
🤖 HMB AI ONLINE

👑 Créateur :
LeRoy HMB

🧠 Intelligence artificielle activée.

📌 Commandes disponibles :
/help
/image
/voice
/reset
/admin
"""

    await update.message.reply_text(txt)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txt = """
📌 COMMANDES

/start
/help
/reset
/image
/voice
/admin

💬 Envoie simplement un message pour discuter avec IA.
"""

    await update.message.reply_text(txt)


async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    memory[user_id] = []

    await update.message.reply_text(
        "🧠 Mémoire supprimée."
    )


async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):

    prompt = " ".join(context.args)

    if not prompt:
        await update.message.reply_text(
            "Utilisation : /image voiture futuriste"
        )
        return

    url = f"https://image.pollinations.ai/prompt/{prompt}"

    await update.message.reply_photo(url)


async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = " ".join(context.args)

    if not text:
        await update.message.reply_text(
            "Utilisation : /voice Bonjour"
        )
        return

    tts = gTTS(text=text, lang="fr")

    tts.save("voice.mp3")

    with open("voice.mp3", "rb") as audio:
        await update.message.reply_voice(audio)


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    users = supabase.table("users").select("*").execute()

    total = len(users.data)

    await update.message.reply_text(
        f"👑 Total utilisateurs : {total}"
    )


async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    blacklist = supabase.table("blacklist").select("*").eq(
        "user_id",
        user_id
    ).execute()

    if blacklist.data:
        return

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
    ] + memory[user_id][-12:]

    headers = {
        "Authorization": f"Bearer {OPENROUTER}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1200
    }

    try:

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        data = r.json()

        response = data["choices"][0]["message"]["content"]

        memory[user_id].append({
            "role": "assistant",
            "content": response
        })

        try:

            supabase.table("history").insert({
                "user_id": user_id,
                "role": "user",
                "content": text
            }).execute()

            supabase.table("history").insert({
                "user_id": user_id,
                "role": "assistant",
                "content": response
            }).execute()

        except Exception:
            pass

        if len(response) > 4000:
            response = response[:4000]

        await update.message.reply_text(response)

    except Exception as e:

        await update.message.reply_text(
            f"❌ Erreur IA : {e}"
        )


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("reset", reset_memory))
app.add_handler(CommandHandler("image", image))
app.add_handler(CommandHandler("voice", voice))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        ai_chat
    )
)

print("HMB AI ONLINE")

app.run_polling()
