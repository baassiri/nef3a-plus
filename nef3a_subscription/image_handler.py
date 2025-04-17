import os
import re
import cv2
import base64
import pytesseract
from telegram import Update
from telegram.ext import ContextTypes
from search_logic import search_by_plate, format_results
from gpt_helper import ask_gpt_image

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\wmmb\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

LOG_FILE = "logs/ocr_gpt_log.txt"
os.makedirs("logs", exist_ok=True)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, authorized_users: set):
    user_id = update.message.from_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("🔐 el code 3mol ma3rouf.")
        return

    photo_file = await update.message.photo[-1].get_file()
    img_path = f"photo_{user_id}.jpg"
    await photo_file.download_to_drive(img_path)

    try:
        await update.message.reply_text("🧠 el m3allim 3am ychouf el soura...")

        # === Step 1: OCR with Tesseract ===
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
        await update.message.reply_text(f"📸 woslit l soura lal el m3allim : `{text.strip()}`", parse_mode="Markdown")

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n---\n🧾 OCR: {text.strip()}\n")

        plate_match = re.search(r"([A-Z])\s?(\d{4,})|(\d{4,})\s?([A-Z])", text.upper())

        # === Step 2: Fallback if OCR fails ===
        if not plate_match:
            await update.message.reply_text("🧠 Soura ma zabta... khallina njarrib tari2a tanye.")
            gpt_result = ask_gpt_image(img_path, "Extract the Lebanese license plate (e.g. 'S 922097').")
            await update.message.reply_text(f"📸 el m3allim ba3do 3ambishuf (2nd try): `{gpt_result}`", parse_mode="Markdown")
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"🔁 Backup result: {gpt_result}\n")
            plate_match = re.search(r"([A-Z])\s?(\d{4,})|(\d{4,})\s?([A-Z])", gpt_result.upper())

        # === Step 3: Search DB
        if plate_match:
            letter = plate_match.group(1) or plate_match.group(4)
            number = plate_match.group(2) or plate_match.group(3)
            plate = f"{number} {letter}"
            await update.message.reply_text(f"🔍 el m3allim 3am yfattesh 3al siyara: `{plate}`", parse_mode="Markdown")

            details = search_by_plate(plate)
            formatted_output = format_results(details)
            await update.message.reply_text(formatted_output)
        else:
            await update.message.reply_text("❌ ma 2idert 2e2ra l ra2m, la Soura wala el tari2a tanye. jarreb soura awda7.")
    finally:
        os.remove(img_path)
