import os

# FatSecret OAuth
CONSUMER_KEY = os.getenv("FATSECRET_CONSUMER_KEY", "")
CONSUMER_SECRET = os.getenv("FATSECRET_CONSUMER_SECRET", "")

# Master tokens obtained via OAuth
MASTER_ACCESS_TOKEN = os.getenv("FATSECRET_MASTER_ACCESS_TOKEN", "")
MASTER_ACCESS_TOKEN_SECRET = os.getenv("FATSECRET_MASTER_ACCESS_SECRET", "")

REQUEST_TOKEN_URL = "https://authentication.fatsecret.com/oauth/request_token"
ACCESS_TOKEN_URL = "https://authentication.fatsecret.com/oauth/access_token"
AUTHORIZE_URL = "https://authentication.fatsecret.com/oauth/authorize"
CALLBACK_URL = "oob"

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Google API
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "")

# Units
TABLESPOON_GRAMS = 15.0
SERVING_GRAMS = 30.0

# USDA API
USDA_API_KEY = os.getenv("USDA_API_KEY", "")

