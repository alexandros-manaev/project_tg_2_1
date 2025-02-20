# fatsecret_api.py

import re
import time
import hmac
import hashlib
import base64
import requests
import random
from urllib.parse import quote
import config  # Абсолютный импорт

def parse_weight(weight_str: str) -> float:
    """
    Извлекает массу продукта из строки и конвертирует в граммы.
    Поддерживает граммы, миллилитры, штуки, ложки (включая "ст л", "столовая ложка", "столовой ложки")
    и порции (например, "1 порция", "3 порции").

    Если в строке присутствуют данные в скобках, например, "(30 г)", функция возвращает число из скобок.
    """
    weight_str = weight_str.replace("\u00A0", " ").lower().strip()

    # Если есть данные в скобках вида "(30 г)"
    paren_match = re.search(r"\((\d+([.,]\d+)?)\s*г", weight_str)
    if paren_match:
        return float(paren_match.group(1).replace(",", "."))

    # Граммы или миллилитры
    match = re.search(r"(\d+([.,]\d+)?)\s*(г|грамм|ml|миллилитр|миллилитров|мл)", weight_str)
    if match:
        value = float(match.group(1).replace(",", "."))
        unit = match.group(3)
        if unit in ["ml", "миллилитр", "миллилитров", "мл"]:
            return value  # 1 мл = 1 г
        return value

    # Штуки
    match = re.search(r"(\d+([.,]\d+)?)\s*(шт|штуки|piece|pieces)", weight_str)
    if match:
        value = float(match.group(1).replace(",", "."))
        return value * 30  # Пример: 1 шт = 30 г

    # Ложки или столовые ложки
    match = re.search(r"(\d+([.,]\d+)?)\s*(ложка|ложки|spoon|spoons|ст\s*л|столовая\s*ложка|столовой\s*ложки)", weight_str)
    if match:
        value = float(match.group(1).replace(",", "."))
        return value * config.TABLESPOON_GRAMS

    # Порции
    match = re.search(r"(\d+([.,]\d+)?)\s*(порция)", weight_str)
    if match:
        value = float(match.group(1).replace(",", "."))
        return value * config.SERVING_GRAMS

    return 0.0

def get_calcium_for_product(product_name: str, access_token: str, access_token_secret: str, product_weight: float = 100.0) -> float:
    """
    Возвращает количество кальция (в мг) для данного продукта с учётом его массы.
    """
    print(f"[DEBUG] Расчет кальция для продукта: {product_name}, масса: {product_weight} г")
    lower_name = product_name.lower()
    base_calcium = 50.0
    if "молоко" in lower_name or "milk" in lower_name:
        base_calcium = 250.0
    elif "кефир" in lower_name or "kefir" in lower_name:
        base_calcium = 200.0
    elif "йогурт" in lower_name or "yogurt" in lower_name or "yoghurt" in lower_name:
        base_calcium = 180.0
    elif "творог" in lower_name or "твор" in lower_name or "cottage" in lower_name:
        base_calcium = 220.0
    elif "рикотта" in lower_name or "ricotta" in lower_name:
        base_calcium = 150.0
    elif "сыр" in lower_name or "cheese" in lower_name:
        base_calcium = 300.0
    elif "сливки" in lower_name or "сметана" in lower_name or "cream" in lower_name:
        base_calcium = 100.0
    calcium = base_calcium * (product_weight / 100.0)
    print(f"[DEBUG] Для '{product_name}' с массой {product_weight} г возвращено значение кальция: {calcium:.2f} мг")
    return calcium

def generate_signature(params: dict, consumer_secret: str, url: str, token_secret: str = "", method: str = "GET") -> str:
    """
    Генерирует OAuth-подпись для запроса.
    """
    sorted_params = sorted(params.items())
    encoded_params = "&".join([quote(str(k), safe="") + "=" + quote(str(v), safe="") for k, v in sorted_params])
    base_string = "&".join([method.upper(), quote(url, safe=""), quote(encoded_params, safe="")])
    signing_key = f"{consumer_secret}&{token_secret}"
    raw = hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    signature = base64.b64encode(raw).decode()
    return signature

# Функции get_fiber_for_product и get_omega3_for_product удалены, так как больше не используются.