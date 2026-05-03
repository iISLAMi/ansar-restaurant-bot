import os

from dotenv import load_dotenv

load_dotenv()
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
PAYMENT_TOKEN = os.getenv('PAYMENT_TOKEN')
