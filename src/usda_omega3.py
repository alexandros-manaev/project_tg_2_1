import requests
import logging
from deep_translator import GoogleTranslator
from config import USDA_API_KEY
import re

logging.basicConfig(level=logging.DEBUG)

SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

FALLBACK_MAPPING = {
    "Сельдь атлантическая": "Fish, herring, Atlantic, raw",
    "Печень трески": "Fish oil, cod liver",
    "Скумбрия": "Fish, mackerel, Atlantic, raw",
    "Иваси": "Pacific sardine",
    "Килька": "Fish, sardine, Atlantic, canned in oil, drained solids with bone",
    "Килька в томатном соусе": "Fish, sardine, Atlantic, canned in oil, drained solids with bone",
    "Сардины в масле": "Sardines, canned in oil",
    "Скумбрия в томатном соусе": "Mackerel, in tomato sauce",
    "Килька соленая": "Fish, sardine, Atlantic, canned in oil, drained solids with bone"
}

OMEGA3_KEYWORDS = {
    "epa": ["20:5 n-3", "eicosapentaenoic", "epa"],
    "dpa": ["22:5 n-3", "docosapentaenoic", "dpa"],
    "dha": ["22:6 n-3", "docosahexaenoic", "dha"]
}

EXCLUDED_KEYWORDS = ["capsule", "supplement", "omega-3"]
ALLOWED_KEYWORDS = ["fish", "canned", "sardine", "sprat", "mackerel", "tuna", "roe"]

def adjust_weight_based_on_canning(food_desc, product_weight):
    if "canned in oil" in food_desc or "in tomato sauce" in food_desc:
        return product_weight * 0.7
    elif "canned in water" in food_desc or "brined" in food_desc:
        return product_weight * 0.9
    return product_weight

def translate_text(text: str) -> str:
    try:
        translated = GoogleTranslator(source="ru", target="en").translate(text)
        return translated.lower()
    except Exception as e:
        logging.error(f"Ошибка перевода '{text}': {e}")
        return text.lower()

def is_red_meat_local(product_name: str) -> bool:
    red_meat_keywords = ["говядин", "свин", "баран", "утят"]
    clean_name = re.sub(r'[\d,\.]', '', product_name).lower()
    return any(keyword in clean_name for keyword in red_meat_keywords)

def search_omega3_components(query: str, product_weight: float) -> float:
    params = {
        "api_key": USDA_API_KEY,
        "query": query,
        "dataType": ["Foundation", "SR Legacy"],
        "pageSize": 20
    }
    logging.debug(f"Отправляем запрос USDA: {query} с параметрами {params}")
    response = None
    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
        if response.status_code == 500:
            logging.debug(f"USDA API вернул 500 для запроса '{query}'. Возвращаем 0.0")
            return 0.0
        response.raise_for_status()
        data = response.json()
        logging.debug(f"Ответ USDA API: {data}")
    except Exception as e:
        logging.error(f"Ошибка запроса USDA API для '{query}': {e}")
        if response is not None and hasattr(response, "text"):
            logging.error(f"Тело ответа: {response.text}")
        return 0.0

    if "foods" not in data or not data["foods"]:
        logging.debug(f"USDA API вернул пустой список продуктов для запроса '{query}'.")
        return 0.0

    for food in data["foods"]:
        food_desc = food.get('description', '').lower()
        if "herring" in query.lower() and "oil" in food_desc:
            logging.debug(f"Пропускаем результат (fish oil) для запроса '{query}': {food_desc}")
            continue
        if any(kw in food_desc for kw in EXCLUDED_KEYWORDS):
            logging.debug(f"Пропускаем продукт по исключающим ключевым словам: {food_desc}")
            continue
        if not any(kw in food_desc for kw in ALLOWED_KEYWORDS):
            logging.debug(f"Пропускаем продукт, т.к. отсутствуют разрешающие ключевые слова: {food_desc}")
            continue

        corrected_weight = adjust_weight_based_on_canning(food_desc, product_weight)
        nutrients = food.get("foodNutrients", [])
        total_omega3 = 0.0

        for nutrient in nutrients:
            nutrient_name = nutrient.get("nutrientName", "").lower()
            value = nutrient.get("value", 0)
            for comp, kw_list in OMEGA3_KEYWORDS.items():
                if any(kw in nutrient_name for kw in kw_list):
                    try:
                        total_omega3 += float(value)
                        logging.debug(f"Найден {comp}: {value} для продукта '{food_desc}'")
                    except (ValueError, TypeError) as e:
                        logging.error(f"Ошибка преобразования значения омега для '{nutrient_name}': {e}")
                        continue

        if total_omega3 > 0:
            result = total_omega3 * (corrected_weight / 100.0)
            logging.debug(f"Расчет омега‑3 для запроса '{query}' с весом {product_weight} г: {result}")
            return result

    logging.debug("Не удалось найти значения омега‑3 в полученных данных USDA API")
    return 0.0

def get_omega3_for_product(product_name: str, product_weight: float = 100.0) -> float:
    if is_red_meat_local(product_name):
        logging.debug(f"Пропускаем USDA API для красного мяса: {product_name}")
        return 0.0

    english_name = translate_text(product_name)
    invalid_words = ["feces", "snack/other", "cholegium", "ural", "sugar"]
    if any(word in english_name for word in invalid_words):
        logging.debug(f"Translated name '{english_name}' содержит недопустимые слова, пропускаем USDA API запрос.")
        return 0.0

    try:
        omega3 = search_omega3_components(english_name, product_weight)
    except Exception as e:
        logging.error(f"Ошибка при получении омега‑3 для '{english_name}': {e}")
        return 0.0

    if omega3 > 0:
        return omega3

    fallback_query = FALLBACK_MAPPING.get(product_name)
    if fallback_query:
        logging.debug(f"Используем fallback для продукта '{product_name}': {fallback_query}")
        try:
            return search_omega3_components(fallback_query, product_weight)
        except Exception as e:
            logging.error(f"Fallback ошибка для '{fallback_query}': {e}")
            return 0.0

    return 0.0