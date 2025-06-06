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
    lower_name = product_name.lower()
    print(f"[DEBUG] Проверяем название продукта: {product_name}, в нижнем регистре: {lower_name}")
    
    # Сначала исключаем альтернативное молоко и продукты с "немолоко"
    alternative_keywords = ["кокос", "соев", "миндал", "овся", "рисов", "немолоко"]
    if any(keyword in lower_name for keyword in alternative_keywords):
        return None

    dairy_keywords = [
        "молоко", "сливки", "ряженка", "кефир", "сливочное масло", "йогурт", "сметана", "творог",
        "кумыс", "мацони", "катык", "варенец", "сыр", "пахта", "простокваша", "творожок", "творожная масса",
        "творожный сыр", "творожная запеканка", "творожный крем", "творожный десерт", "творожный пудинг", "творожный суп",
        "творожный соус", "творожный кекс", "творожный пирог", "творожный кулич", "творожный мусс", "творожный крем-суп",
        "творожный крем-супчик", "творожный крем-супчишко", "творожный крем-супчище",
        "пармезан", "моцарелла", "тарак", "шубат", "спред", "айран", "молочная сыворотка", "молочный коктейль",
        "латте", "капучино", "рафф",
        "milk", "cream", "sour cream", "yogurt", "butter", "cheese", "kefir", "curd", "whey", "milkshake", "latte", "cappuccino"
    ]
    if any(keyword in lower_name for keyword in dairy_keywords):
        return "milk"
    return None
