import os
import base64
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_gpt_image(img_path: str, prompt: str) -> str:
    with open(img_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}}
                ]
            }
        ],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

def ask_gpt_audio(audio_path: str) -> str:
    # Step 1: Transcribe voice to text
    with open(audio_path, "rb") as file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=file
        ).text

    # Step 2: Extract license plate from transcript
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a Lebanese license plate assistant."},
            {"role": "user", "content": f"The user said: '{transcript}'. Extract and return only the license plate in this format: 'S 188278' or '188278 S'. Reply with only the plate."}
        ],
        max_tokens=100
    )

    print("🧠 Transcribed:", transcript)
    print("🧠 El M3allim's Final Answer:", response.choices[0].message.content)

    return response.choices[0].message.content.strip()
