import os
import asyncio
import requests
from gtts import gTTS
from dotenv import load_dotenv
from supabase import create_client, Client

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# =========================================
# LOAD ENV
# =========================================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER = os.getenv("OPENROUTER_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# =========================================
# SUPABASE CONFIG
# =========================================

SUPABASE_URL = "https://oamwhotabmukzciuzvsn.supabase.co"

SUPABASE_KEY = "sb_secret_sx1b8SLsKELkCu5_I-o_YQ_a4dl7Xcy"

# =========================================
# SUPABASE CLIENT
# =========================================

supabase = None

try:
    supabase: Client = create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

    print("✅ Supabase connecté")

except Exception as e:

    print(f"❌ Erreur Supabase : {e}")

# =========================================
# MEMORY
# =========================================

memory = {}

# =========================================
# SYSTEM PROMPT
# =========================================

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

# =========================================
# START
# =========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if supabase:

        try:

            supabase.table("users").upsert({
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name
            }).execute()

        except Exception as e:

            print(f"Erreur users table : {e}")

    txt = """
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

# =========================================
# HELP
# =========================================

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

# =========================================
# RESET MEMORY
# =========================================

async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    memory[user_id] = []

    await update.message.reply_text(
        "🧠 Mémoire supprimée."
    )

# =========================================
# IMAGE
# =========================================

async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):

    prompt = " ".join(context.args)

    if not prompt:

        await update.message.reply_text(
            "Utilisation : /image voiture futuriste"
        )

        return

    url = f"https://image.pollinations.ai/prompt/{prompt}"

    await update.message.reply_photo(url)

# =========================================
# VOICE
# =========================================

async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = " ".join(context.args)

    if not text:

        await update.message.reply_text(
            "Utilisation : /voice Bonjour"
        )

        return

    tts = gTTS(
        text=text,
        lang="fr"
    )

    tts.save("voice.mp3")

    with open("voice.mp3", "rb") as audio:

        await update.message.reply_voice(audio)

# =========================================
# ADMIN
# =========================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != OWNER_ID:
        return

    if not supabase:

        await update.message.reply_text(
            "❌ Supabase non connecté."
        )

        return

    try:

        users = supabase.table("users").select("*").execute()

        total = len(users.data)

        await update.message.reply_text(
            f"👑 Total utilisateurs : {total}"
        )

    except Exception as e:

        await update.message.reply_text(
            f"❌ Erreur admin : {e}"
        )

# =========================================
# AI CHAT
# =========================================

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text

    # =========================================
    # BLACKLIST
    # =========================================

    if supabase:

        try:

            blacklist = supabase.table("blacklist").select("*").eq(
                "user_id",
                user_id
            ).execute()

            if blacklist.data:
                return

        except Exception as e:

            print(f"Erreur blacklist : {e}")

    # =========================================
    # MEMORY
    # =========================================

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

        # =========================================
        # SAVE HISTORY
        # =========================================

        if supabase:

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

            except Exception as e:

                print(f"Erreur history : {e}")

        if len(response) > 4000:
            response = response[:4000]

        await update.message.reply_text(response)

    except Exception as e:

        await update.message.reply_text(
            f"❌ Erreur IA : {e}"
        )

# =========================================
# MAIN APP
# =========================================

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

# =========================================
# START BOT
# =========================================

print("🤖 HMB AI ONLINE")

if __name__ == "__main__":

    asyncio.set_event_loop(
        asyncio.new_event_loop()
    )

    app.run_polling(
        close_loop=False
        )
