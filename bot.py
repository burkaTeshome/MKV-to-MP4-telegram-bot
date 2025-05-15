import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import ffmpeg
import logging

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token from BotFather
TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm a bot that converts MKV to MP4. Send me an MKV file, and I'll convert it for you!"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    if not file:
        await update.message.reply_text("Please send an MKV file.")
        return

    # Check if the file is an MKV
    if not file.file_name.lower().endswith(".mkv"):
        await update.message.reply_text("Please send a valid MKV file.")
        return

    # Download the file
    file_obj = await context.bot.get_file(file.file_id)
    input_path = f"temp_{file.file_name}"
    output_path = f"temp_{file.file_name[:-4]}.mp4"

    try:
        # Download the file
        await file_obj.download_to_drive(input_path)
        await update.message.reply_text("Converting your MKV to MP4...")

        # Convert MKV to MP4 using FFmpeg
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

        # Send the converted file
        with open(output_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=file.file_name[:-4] + ".mp4",
                caption="Here’s your converted MP4 file!"
            )

        await update.message.reply_text("Conversion complete!")

    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        await update.message.reply_text("Sorry, an error occurred during conversion.")

    finally:
        # Clean up temporary files
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    await update.message.reply_text("An error occurred. Please try again.")

def main():
    # Initialize the bot
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()