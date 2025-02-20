# src/auth.py
import time
import hmac
import hashlib
import base64
import requests
import logging
from urllib.parse import quote
import config  # Абсолютный импорт

logging.basicConfig(level=logging.INFO)

# Глобальное хранилище токенов пользователей
user_tokens = {}

def generate_signature(params, consumer_secret, url, token_secret="", method="POST"):
    # Сортировка параметров
    sorted_params = sorted(params.items())
    query_string = "&".join(f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in sorted_params)
    base_string = "&".join([
        method.upper(),
        quote(url, safe=""),
        quote(query_string, safe="")
    ])
    signing_key = f"{consumer_secret}&{token_secret}"
    raw = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    return base64.b64encode(raw).decode()

def get_request_token():
    logging.info("Отправляем запрос на получение Request Token...")
    oauth_timestamp = str(int(time.time()))
    oauth_nonce = str(int(time.time() * 1000))
    params = {
        "oauth_consumer_key": config.CONSUMER_KEY,
        "oauth_nonce": oauth_nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": oauth_timestamp,
        "oauth_version": "1.0",
        "oauth_callback": config.CALLBACK_URL
    }
    signature = generate_signature(params, config.CONSUMER_SECRET, config.REQUEST_TOKEN_URL)
    params["oauth_signature"] = signature
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(config.REQUEST_TOKEN_URL, data=params, headers=headers, timeout=10)
        logging.info(f"Ответ от FatSecret: {response.status_code} - {response.text}")
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса к FatSecret API: {str(e)}")
        return "ERROR"

def get_access_token(oauth_token, oauth_token_secret, oauth_verifier):
    logging.info("Обмениваем Request Token на Access Token...")
    oauth_timestamp = str(int(time.time()))
    oauth_nonce = str(int(time.time() * 1000))
    params = {
        "oauth_consumer_key": config.CONSUMER_KEY,
        "oauth_token": oauth_token,
        "oauth_verifier": oauth_verifier,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": oauth_timestamp,
        "oauth_nonce": oauth_nonce,
        "oauth_version": "1.0"
    }
    signature = generate_signature(params, config.CONSUMER_SECRET, config.ACCESS_TOKEN_URL, token_secret=oauth_token_secret)
    params["oauth_signature"] = signature
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(config.ACCESS_TOKEN_URL, data=params, headers=headers, timeout=10)
        logging.info(f"Ответ от FatSecret: {response.status_code} - {response.text}")
        return response.text
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса к FatSecret API: {str(e)}")
        return "ERROR"
