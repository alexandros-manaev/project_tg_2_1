import time
import hmac
import hashlib
import base64
import requests
import webbrowser
from urllib.parse import quote

# Вставьте сюда свои ключи (consumer key и consumer secret), полученные от FatSecret
CONSUMER_KEY = "b24c8716c77d48bd8857f20cdae26271"
CONSUMER_SECRET = "120cc0911fc04af2a55c3f0c07508abd"

# URL-адреса для OAuth-процесса
REQUEST_TOKEN_URL = "https://authentication.fatsecret.com/oauth/request_token"
ACCESS_TOKEN_URL = "https://authentication.fatsecret.com/oauth/access_token"
AUTHORIZE_URL = "https://authentication.fatsecret.com/oauth/authorize"
CALLBACK_URL = "oob"  # out-of-band – используется для PIN-кода

def generate_signature(params, consumer_secret, url, token_secret="", method="POST"):
    sorted_params = sorted(params.items())
    query_string = "&".join(f"{quote(str(k), safe='')}={quote(str(v), safe='')}" for k, v in sorted_params)
    base_string = "&".join([method.upper(), quote(url, safe=""), quote(query_string, safe="")])
    signing_key = f"{consumer_secret}&{token_secret}"
    raw = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    return base64.b64encode(raw).decode()

def get_request_token():
    oauth_timestamp = str(int(time.time()))
    oauth_nonce = str(int(time.time() * 1000))
    params = {
        "oauth_consumer_key": CONSUMER_KEY,
        "oauth_nonce": oauth_nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": oauth_timestamp,
        "oauth_version": "1.0",
        "oauth_callback": CALLBACK_URL
    }
    signature = generate_signature(params, CONSUMER_SECRET, REQUEST_TOKEN_URL)
    params["oauth_signature"] = signature

    response = requests.post(REQUEST_TOKEN_URL, data=params)
    if response.status_code != 200:
        print("Ошибка получения request token:", response.text)
        exit(1)
    return response.text

def get_access_token(oauth_token, oauth_token_secret, oauth_verifier):
    oauth_timestamp = str(int(time.time()))
    oauth_nonce = str(int(time.time() * 1000))
    params = {
        "oauth_consumer_key": CONSUMER_KEY,
        "oauth_token": oauth_token,
        "oauth_verifier": oauth_verifier,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": oauth_timestamp,
        "oauth_nonce": oauth_nonce,
        "oauth_version": "1.0"
    }
    signature = generate_signature(params, CONSUMER_SECRET, ACCESS_TOKEN_URL, token_secret=oauth_token_secret)
    params["oauth_signature"] = signature

    response = requests.post(ACCESS_TOKEN_URL, data=params)
    if response.status_code != 200:
        print("Ошибка получения access token:", response.text)
        exit(1)
    return response.text

def main():
    # 1. Получаем request token
    print("Получение Request Token...")
    token_response = get_request_token()
    if "oauth_token=" not in token_response:
        print("Неправильный ответ от FatSecret:", token_response)
        exit(1)
    oauth_token = token_response.split("oauth_token=")[1].split("&")[0]
    oauth_token_secret = token_response.split("oauth_token_secret=")[1].split("&")[0]
    
    # 2. Формируем URL для авторизации и открываем его в браузере
    auth_url = f"{AUTHORIZE_URL}?oauth_token={oauth_token}"
    print("Откройте следующую ссылку для авторизации в вашем браузере:")
    print(auth_url)
    webbrowser.open(auth_url)
    
    # 3. После авторизации в FatSecret вам будет показан PIN-код.
    oauth_verifier = input("Введите полученный PIN-код: ").strip()
    
    # 4. Обмениваем Request Token и PIN-код на Access Token
    access_response = get_access_token(oauth_token, oauth_token_secret, oauth_verifier)
    if "oauth_token=" not in access_response:
        print("Ошибка авторизации:", access_response)
        exit(1)
    
    access_token = access_response.split("oauth_token=")[1].split("&")[0]
    access_token_secret = access_response.split("oauth_token_secret=")[1].split("&")[0]
    
    print("\nМастер токены получены!")
    print("Access Token:", access_token)
    print("Access Token Secret:", access_token_secret)
    print("\nСкопируйте эти значения и вставьте в ваш файл config.py.")

if __name__ == "__main__":
    main()
