# Telegram Nutrition Bot

This repository contains a Telegram bot that helps track omega‑3 intake and analyse daily food reports.

## Setup

1. Create a Python virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Provide the required API keys via environment variables:

- `TELEGRAM_BOT_TOKEN` – token for your Telegram bot
- `FATSECRET_CONSUMER_KEY` and `FATSECRET_CONSUMER_SECRET` – credentials for the FatSecret API
- `FATSECRET_MASTER_ACCESS_TOKEN` and `FATSECRET_MASTER_ACCESS_SECRET` – OAuth access token/secret
- `GOOGLE_CREDENTIALS_JSON` – path to the Google service account JSON file
- `GOOGLE_SPREADSHEET_ID` – ID of the Google Sheet used for logging
- `USDA_API_KEY` – API key for the USDA service

3. Run the bot:

```bash
python -m src.main
```

## Development

Unit tests are located in the `tests` folder and can be run with `python -m unittest`.

All temporary files, credentials and caches are excluded via `.gitignore`.

