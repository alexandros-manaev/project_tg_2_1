# src/config.py

# FatSecret OAuth данные
CONSUMER_KEY = "b24c8716c77d48bd8857f20cdae26271"
CONSUMER_SECRET = "120cc0911fc04af2a55c3f0c07508abd"

# Мастер токены, полученные через get_master_token.py
MASTER_ACCESS_TOKEN = "d67ddb530b5440fc94ba6e5cd90826ac"
MASTER_ACCESS_TOKEN_SECRET = "25f7fcdb9d2d47e0abc0a95a5d309bf6"

# Остальные настройки...
REQUEST_TOKEN_URL = "https://authentication.fatsecret.com/oauth/request_token"
ACCESS_TOKEN_URL = "https://authentication.fatsecret.com/oauth/access_token"
AUTHORIZE_URL = "https://authentication.fatsecret.com/oauth/authorize"
CALLBACK_URL = "oob"

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7120699779:AAFr7kZ0PN8zbtWu0_I29uPBH93A1pzj_YA"

# Настройки Google API (если используются)
GOOGLE_CREDENTIALS_JSON = "/Users/aleksandr/Yandex.Disk.localized/project/credentials/credentials.json"
GOOGLE_SPREADSHEET_ID = "1Ar-uwpWS57WqnpNfD2nH4r21tfPrSg6pp0lkeCaPrEw"

# Настройки для единиц измерения:
TABLESPOON_GRAMS = 15.0   # количество грамм в одной столовой ложке
SERVING_GRAMS = 30.0      # количество грамм в одной порции

# USDA
USDA_API_KEY = "tdaYcNceK7GYfT6EODTviCxGJBjEONI62dgSH2IA"