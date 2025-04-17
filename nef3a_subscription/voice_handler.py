import os
import re
import tempfile
from telegram import Update
from telegram.ext import ContextTypes
from search_logic import search_by_plate, format_results
from gpt_helper import ask_gpt_audio  # Now only 1 argument passed

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE, authorized_users: set):
    user_id = update.message.from_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("🔐 el code 3mol ma3rouf.")
        return

    voice = await update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
        await voice.download_to_drive(custom_path=tmp_file.name)
        audio_path = tmp_file.name

    try:
        # Convert OGG to MP3 for GPT
        mp3_path = audio_path.replace(".ogg", ".mp3")
        os.system(f"ffmpeg -i {audio_path} {mp3_path} -y -loglevel quiet")

        await update.message.reply_text("🎧 el m3allim 3am ysamé3 el voice...")

        # Call ask_gpt_audio with 1 argument
        plate_raw = ask_gpt_audio(mp3_path)
        await update.message.reply_text(f"🎤 el m3allim samé3a: `{plate_raw}`", parse_mode="Markdown")

        # Clean and extract plate from GPT result
        match = re.search(r"([A-Z])\s?(\d{4,})|(\d{4,})\s?([A-Z])", plate_raw.upper())
        if match:
            letter = match.group(1) or match.group(4)
            number = match.group(2) or match.group(3)
            plate = f"{number} {letter}"

            await update.message.reply_text(f"🔍 el m3allim 3am yfattesh 3al siyara: `{plate}`", parse_mode="Markdown")
            details = search_by_plate(plate)
            formatted_output = format_results(details)
            await update.message.reply_text(formatted_output)
        else:
            await update.message.reply_text("❌ ma 2idert 2e2ra l ra2m mn el voicenote, rja3 m3at wahde awdah 3mol ma3rouf.")
    finally:
        os.remove(audio_path)
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
