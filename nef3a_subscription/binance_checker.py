from binance.client import Client
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import sqlite3
from sqlite3 import Error
load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_SECRET_KEY)

# Stores processed transaction IDs (txId)
processed_tx_ids = set()

def check_usdt_payment(min_amount: float = 10) -> dict:
    try:
        deposits = client.get_deposit_history(asset='USDT')
        now = datetime.utcnow()

        for dep in deposits:
            tx_id = dep.get('txId')

            if (
                dep['status'] == 1 and  # Success
                float(dep['amount']) == float(min_amount) and
                datetime.fromtimestamp(dep['insertTime'] / 1000) > now - timedelta(minutes=10) and
                tx_id not in processed_tx_ids
            ):
                processed_tx_ids.add(tx_id)
                return {
                    "amount": float(dep['amount']),
                    "tx_id": tx_id,
                    "time": dep['insertTime']
                }

        return None
    except Exception as e:
        print("❌ Binance check failed:", e)
        return None
