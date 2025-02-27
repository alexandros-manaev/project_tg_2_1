import re
import logging
from fatsecret_api import parse_weight

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def filter_red_meat_products(products):
    red_meat_keywords = ["говядин", "свин", "баран", "утят"]
    filtered = []
    for product, weight, protein in products:
        lower_name = product.lower()
        clean_name = re.sub(r'[\d,\.]', '', lower_name)
        if any(keyword in clean_name for keyword in red_meat_keywords) and protein:
            filtered.append((product, weight, protein))
    return filtered

def handle_red_meat(products):
    red_meat_products = filter_red_meat_products(products)
    total_weight = 0.0
    total_protein = 0.0
    for product, weight_str, protein_str in red_meat_products:
        try:
            weight = float(weight_str.replace("г", "").strip())
        except Exception as e:
            logging.warning(f"Не удалось определить вес для '{product}': {e}")
            weight = 0.0
        try:
            protein = float(protein_str.replace(",", "."))
        except Exception as e:
            logging.warning(f"Не удалось определить белок для '{product}': {e}")
            protein = 0.0
        total_weight += weight
        total_protein += protein
        logging.debug(f"[DEBUG] Red meat: '{product}' -> вес: {weight} г, белок: {protein} г")
    portions = total_protein / 25.0 if total_protein > 0 else 0.0
    return total_weight, total_protein, portions

def red_meat_message(total_weight, total_protein, portions):
    if total_weight == 0:
        return "Вы не потребляли красное мясо за неделю. Рекомендуем добавить его в рацион."
    if total_weight > 700:
        return f"Вы превысили рекомендуемую норму красного мяса (700 г)! Потреблено {total_weight:.0f} г."
    return (f"Потреблено {total_weight:.0f} г красного мяса, содержащего {total_protein:.1f} г белка, "
            f"что соответствует примерно {portions:.1f} порциям (1 порция = 25 г белка).")