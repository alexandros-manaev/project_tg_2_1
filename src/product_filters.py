# src/product_filters.py

def filter_dairy_products(products, api_categories):
    dairy_products = []
    for product, weight, *rest in products:
        print(f"[DEBUG] Обрабатываем продукт: {product} с массой {weight}")
        dairy_class = classify_dairy_product(product, api_categories)
        if dairy_class:
            dairy_products.append((product, weight, dairy_class))
    print(f"[DEBUG] Отфильтрованные молочные продукты: {dairy_products}")
    return dairy_products

def classify_dairy_product(product_name, api_category=None):
    """
    Классифицирует продукт как молочный, если название содержит ключевые слова, относящиеся к молочным продуктам.
    Добавлены "молоко", "milk" и производные названия.
    """
    lower_name = product_name.lower()
    print(f"[DEBUG] Проверяем название продукта: {product_name}, в нижнем регистре: {lower_name}")

    dairy_keywords = [
        # Основные молочные продукты:
        "молоко", "сливки", "ряженка", "кефир", "сливочное масло", "йогурт", "сметана", "творог", "кумыс", "мацони", "катык", "варенец", "сыр",
        "пахта", "простокваша",
        # Дополнительные продукты:
        "пармезан", "моцарелла", "тарак", "шубат", "спред", "айран", "молочная сыворотка", "молочный коктейль",
        # Кофейные напитки:
        "латте", "капучино", "рафф",
        # Альтернативные английские названия:
        "milk", "cream", "sour cream", "yogurt", "butter", "cheese", "kefir", "curd", "whey", "milkshake", "latte", "cappuccino"
    ]

    if any(keyword in lower_name for keyword in dairy_keywords):
        return "milk"

    return None