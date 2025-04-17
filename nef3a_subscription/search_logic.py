import re
import sqlite3
import openai
from dotenv import load_dotenv
import os
from telegram import Update

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

DB_PATH = r"C:\Users\wmmb\OneDrive\Desktop\Projects\nef3a plus\data\converted.sqlite"

def format_results(d: dict) -> str:
    if d:
        return (
            f"🚗 Plate: {d.get('plate')}\n"
            f"🧾 Reg #: {d.get('reg_number')}\n"
            f"👤 Name: {d.get('name')}\n"
            f"👵 Mother: {d.get('mother')}\n"
            f"📞 Phone: {d.get('phone')}\n"
            f"🎂 DOB: {d.get('dob')}\n"
            f"🌍 Birthplace: {d.get('birthplace')}\n"
            f"🏠 Address: {d.get('address')}\n"
            f"🏘️ District ID: {d.get('district')}\n"
            f"🌆 City ID: {d.get('city')}\n"
            f"🏛️ Governate ID: {d.get('governate')}\n"
            f"🚘 Car: {d.get('car')}\n"
            f"🎨 Color: {d.get('color')}\n"
            f"🔩 Chassis: {d.get('chassis')}\n"
            f"🔑 Engine: {d.get('engine')}\n"
            f"📆 Acquired: {d.get('acquisition_date')}\n"
            f"📆 1st Registration: {d.get('first_registration')}\n"
            f"⚠️ Status: {d.get('status')}\n"
        )
    return "❌ No data found."

def search_by_plate(input_text: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cleaned = input_text.replace(" ", "").upper()

    match = re.match(r"(\d+)([A-Z])", cleaned) or re.match(r"([A-Z])(\d+)", cleaned)
    if match:
        number = match.group(1) if match.group(1).isdigit() else match.group(2)
        letter = match.group(2) if match.group(1).isdigit() else match.group(1)
    else:
        conn.close()
        return None

    query = """
    SELECT * FROM CARMDI
    WHERE REPLACE(CAST(ActualNB AS TEXT), ' ', '') = ?
    AND REPLACE(CodeDesc, ' ', '') = ?
    LIMIT 1
    """
    cursor.execute(query, (number, letter))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "plate": f"{row[0]} {row[1]}",
            "year": row[2],
            "name": f"{row[13]} {row[14]}",
            "phone": row[21],
            "car": f"{row[8]} {row[10]}",
            "color": row[7],
            "address": row[16],
            "dob": row[22],
            "birthplace": row[23],
            "chassis": row[3],
            "engine": row[4],
            "acquisition_date": row[5],
            "first_registration": row[6],
            "reg_number": row[15],
            "mother": row[20],
            "district": row[18],
            "city": row[17],
            "governate": row[19],
            "status": row[24]
        }

    return None


async def handle_search(update, context):
    plate_number = update.message.text.strip()
    print(f"🔍 Searching for: {plate_number}")
    details = smart_search(plate_number)

    formatted_output = format_results(details)
    await update.message.reply_text(formatted_output)

async def ask_gpt_image(img_path: str, prompt: str) -> str:
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=50
    )
    return response.choices[0].text.strip()

async def handle_more(update, context):
    await update.message.reply_text("🔍 Here's more information related to your search.")
def smart_search(input_text: str) -> dict | None:
    cleaned = input_text.replace(" ", "").upper()

    # Check if it's a license plate
    if re.match(r"\d+[A-Z]$|[A-Z]\d+$", cleaned):
        return search_by_plate(input_text)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check for phone
    cursor.execute("SELECT * FROM CARMDI WHERE TelProp = ?", (input_text,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return build_result(row)

    # Check for name
    parts = input_text.strip().split()
    if len(parts) >= 2:
        fname, lname = parts[0], parts[1]
        cursor.execute("SELECT * FROM CARMDI WHERE OwnerFirstName = ? AND OwnerLastName = ?", (fname, lname))
        row = cursor.fetchone()
        if row:
            conn.close()
            return build_result(row)

    conn.close()
    return None

def build_result(row):
    return {
        "plate": f"{row[0]} {row[1]}",
        "year": row[2],
        "name": f"{row[13]} {row[14]}",
        "phone": row[21],
        "car": f"{row[8]} {row[10]}",
        "color": row[7],
        "address": row[16],
        "dob": row[22],
        "birthplace": row[23],
        "chassis": row[3],
        "engine": row[4],
        "acquisition_date": row[5],
        "first_registration": row[6],
        "reg_number": row[15],
        "mother": row[20],
        "district": row[18],
        "city": row[17],
        "governate": row[19],
        "status": row[24]
    }
