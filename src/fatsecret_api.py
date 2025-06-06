import re
import time
import hmac
import hashlib
import base64
import requests
import random
from urllib.parse import quote
import config
import logging

def parse_weight(weight_str: str) -> float:
    weight_str = weight_str.replace("\u00A0", " ").lower().strip()
    paren_match = re.search(r"\((\d+([.,]\d+)?)\s*г", weight_str)
    if paren_match:
        return float(paren_match.group(1).replace(",", "."))
    match = re.search(r"(\d+([.,]\d+)?)\s*(г|грамм|ml|миллилитр|миллилитров|мл)", weight_str)
    if match:
        value = float(match.group(1).replace(",", "."))
        unit = match.group(3)
        if unit in ["ml", "миллилитр", "миллилитров", "мл"]:
            return value
        return value
    match = re.search(r"(\d+([.,]\d+)?)\s*(шт|штуки|piece|pieces)", weight_str)
    if match:
        value = float(match.group(1).replace(",", "."))
        return value * 30
    match = re.search(r"(\d+([.,]\d+)?)\s*(ложка|ложки|spoon|spoons|ст\s*л|столовая\s*ложка|столовой\s*ложки)", weight_str)
    if match:
        value = float(match.group(1).replace(",", "."))
        return value * config.TABLESPOON_GRAMS
    match = re.search(r"(\d+([.,]\d+)?)\s*(порция)", weight_str)
    if match:
        value = float(match.group(1).replace(",", "."))
        return value * config.SERVING_GRAMS
    return 0.0

def get_calcium_for_product(product_name: str, access_token: str, access_token_secret: str, product_weight: float = 100.0) -> float:
    logging.debug(f"[DEBUG] Расчет кальция для продукта: {product_name}, масса: {product_weight} г")
    lower_name = product_name.lower()
    # Если продукт относится к альтернативному молоку или содержит слово "немолоко"
    alternative_keywords = ["кокос", "соев", "миндал", "овся", "рисов", "немолоко"]
    if any(keyword in lower_name for keyword in alternative_keywords):
        base_calcium = 50.0
    elif "молоко" in lower_name or "milk" in lower_name:
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
    else:
        base_calcium = 50.0
    calcium = base_calcium * (product_weight / 100.0)
    logging.debug(f"[DEBUG] Для '{product_name}' с массой {product_weight} г возвращено значение кальция: {calcium:.2f} мг")
    return calcium