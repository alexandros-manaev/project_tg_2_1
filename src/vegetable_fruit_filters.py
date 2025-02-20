# vegetable_fruit_filters.py

from fatsecret_api import parse_weight
import config  # Импорт конфигурации при необходимости

def filter_vegetable_and_fruit_products(products):
    vegetable_and_fruit_products = []
    for product, weight, *rest in products:
        print(f"[DEBUG] Обрабатываем продукт: {product} с массой {weight}")
        product_class = classify_vegetable_and_fruit_product(product)
        if product_class:
            vegetable_and_fruit_products.append((product, weight, product_class))
    print(f"[DEBUG] Отфильтрованные растительные продукты: {vegetable_and_fruit_products}")
    return vegetable_and_fruit_products

def classify_vegetable_and_fruit_product(product_name):
    """
    Классифицирует продукт как растительный (овощи, фрукты, ягоды, грибы, зелень, травы, овощные смеси)
    или нет. Исключаются продукты, содержащие признаки молочной продукции.
    """
    lower_name = product_name.lower()
    print(f"[DEBUG] Проверяем название продукта: {product_name}, в нижнем регистре: {lower_name}")
    
    # Исключения – молочные продукты
    dairy_exclusions = ["творог", "творожок", "сыр", "молоко", "кефир", "йогурт"]
    if any(dairy_kw in lower_name for dairy_kw in dairy_exclusions):
        return None
    
    plant_keywords = [
        "яблоко", "банан", "апельсин", "груша", "киви", "манго", "персик", "слива", "лимон", "ананас", "виноград",
        "грейпфрут", "абрикос", "инжир", "гранат", "папайя", "авокадо", "клубника", "черника", "малина", "ежевика",
        "капуста", "морковь", "огурец", "помидор", "редис", "лук", "чеснок", "перец", "болгарский", "баклажан", "сельдерей",
        "спаржа", "брокколи", "цветная капуста",
        "смесь овощная", "овощная смесь",
        "ягода",
        "гриб", "шампиньон", "лисичка", "белый гриб", "подосиновик", "сморчок", "опёнок",
        "зелень", "петрушка", "укроп", "розмарин", "тимьян", "базилик", "мята", "зелёный лук", "листья", "травы", "шпинат", "руккола", "салат", "крапива", "латук", "кинза"
    ]
    exclusion_keywords = ["джем", "варенье", "конфитюр", "сок", "пюре", "компот", "консерв"]
    if any(kw in lower_name for kw in exclusion_keywords):
        return None
    if any(keyword in lower_name for keyword in plant_keywords):
        return "plant"
    return None

def handle_vegetables_and_fruits(products):
    total_weight = 0.0  # Суммарная масса растительной продукции

    plant_products = filter_vegetable_and_fruit_products(products)
    
    for product, weight, product_class in plant_products:
        product_weight = parse_weight(weight)
        total_weight += product_weight
        print(f"[DEBUG] Продукт: {product}, масса: {weight}")

    print(f"[DEBUG] Общая масса растительной продукции: {total_weight:.2f} г")

    if total_weight < 400:
        message = "Вы сильно не добираете растительности."
    elif 400 <= total_weight < 600:
        message = "Неплохо, но вы немного не добираете растительности."
    else:
        message = "Норма выполнена."

    return total_weight, message