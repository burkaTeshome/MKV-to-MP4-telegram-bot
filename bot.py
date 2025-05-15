import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from aiohttp import web
import ffmpeg
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PORT = int(os.getenv("PORT", 8443))  # Render assigns PORT
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-app.onrender.com

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm a bot that converts MKV to MP4. Send me an MKV file!"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if not file:
        await update.message.reply_text("Please send an MKV file.")
        return
    if not file.file_name.lower().endswith(".mkv"):
        await update.message.reply_text("Please send a valid MKV file.")
        return

    file_obj = await context.bot.get_file(file.file_id)
    input_path = f"temp_{file.file_name}"
    output_path = f"temp_{file.file_name[:-4]}.mp4"

    try:
        await file_obj.download_to_drive(input_path)
        await update.message.reply_text("Converting your MKV to MP4...")

        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(
            stream,
            output_path,
            vcodec="libx264",
            acodec="aac",
            pix_fmt="yuv420p",
            format="mp4",
            loglevel="quiet",
        )
        ffmpeg.run(stream)

        with open(output_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=file.file_name[:-4] + ".mp4",
                caption="Here’s your converted MP4 file!"
            )
        await update.message.reply_text("Conversion complete!")

    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        await update.message.reply_text("Sorry, an error occurred.")

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    await update.message.reply_text("An error occurred. Please try again.")

async def webhook_handler(request):
    update = Update.de_json(await request.json(), app.bot)
    await app.process_update(update)
    return web.Response()

async def setup_webhook():
    await app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")

app = None  # Global for webhook_handler

def main():
    global app
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_error_handler(error_handler)

    web_app = web.Application()
    web_app.router.add_post("/webhook", webhook_handler)

    # Run the server
    web.run_app(web_app, host="0.0.0.0", port=WEBHOOK_PORT, loop=app.loop)

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(setup_webhook())
    main()