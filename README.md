# Nef3a Plus 🚗🕵️

**Nef3a Plus** is a powerful Telegram bot that helps users search for vehicle data using multiple methods including license plates, phone numbers, names (Arabic + English transliteration), car types, car brands, and more.

### 🔍 Features

- License plate and phone number lookup
- Name matching in Arabic + English (Yamli transliteration support)
- Image OCR support for license plates and documents
- Voice note recognition and search
- Admin panel with access control and subscription verification
- Binance USDT wallet integration for payment and access
- Funny Lebanese-style chatbot replies (e.g. "el m3allim")

### ⚙️ Technologies Used

- Python 3.9
- Telegram Bot API (`python-telegram-bot`)
- OpenCV + Tesseract OCR
- SQLite for local database
- dotenv for config
- Binance API (for automated USDT payment verification)
- Yamli API (for Arabic-English name matching)

### 📂 Project Structure
nef3a_plus/ │ ├── nef3a/ # Main bot handlers (free bot) ├── nef3a_subscription/ # Subscription-only bot ├── venv_DMV/ # (ignored) Virtual environment ├── data/ # (ignored) Local database files ├── logs/ # (ignored) Bot logs │ ├── .env.example # Template for secrets ├── .gitignore # Ignored folders & files ├── requirements.txt # Python dependencies ├── Dockerfile # Optional Docker support ├── main.py # Launcher script └── README.md #


### 🚀 How to Run

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
Install dependencies:

pip install -r requirements.txt
python main.py
Made with ❤️ in Lebanon 🇱🇧 by Yerba_M

csharp
Copy
Edit

Copy this and save it as `README.md` inside your project folder, then:

```bash
git add README.md
git commit -m "Add README with project description"
git push

you can add this bot on telegram @Nef3as_bot, pay and enjoy!
