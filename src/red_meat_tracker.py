from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Часть 1. Расчёт по данным красного мяса ---

def filter_red_meat_products(products):
    """
    Из входного списка продуктов (формат: [(название, вес_строкой, protein), ...])
    отбирает те, которые относятся к красному мясу.
    Ключевые слова: 'говядин', 'свин', 'баран', 'утят'
    В расчет берется только тот продукт, для которого извлечена конкретная цифра белка.
    """
    red_meat_keywords = ["говядин", "свин", "баран", "утят"]
    filtered = []
    for item in products:
        name = item[0].lower()
        # Если название содержит ключевое слово и указано значение белка (не None)
        if any(kw in name for kw in red_meat_keywords) and item[2] is not None:
            filtered.append(item)
    return filtered

def handle_red_meat(products):
    """
    Обрабатывает список красного мяса.
    Извлекает суммарный вес (в граммах) и суммарное количество белка (г) 
    только для тех продуктов, где информация о белке явно указана.
    
    Ожидаемый формат входного списка: 
      [(название, вес_строкой, protein), ...]
    Возвращает: total_weight (г), total_protein (г), portions (total_protein/25)
    """
    total_weight = 0.0
    total_protein = 0.0
    red_meat = filter_red_meat_products(products)
    
    for item in red_meat:
        name, weight_str, protein = item
        try:
            weight = float(weight_str.replace("г", "").strip())
        except Exception:
            logging.warning(f"Не удалось определить вес для продукта {name}. Пропускаем.")
            continue
        try:
            protein_value = float(protein)
        except Exception:
            logging.warning(f"Не удалось определить белок для продукта {name}. Пропускаем.")
            continue
        total_weight += weight
        total_protein += protein_value
        logging.debug(f"Продукт: {name}, вес: {weight} г, белок: {protein_value:.1f} г")
    
    # Количество порций рассчитывается исходя из белка: 1 порция = 25 г белка
    portions = total_protein / 25.0 if total_protein > 0 else 0.0
    return total_weight, total_protein, portions

def red_meat_message(total_weight, total_protein, portions):
    """
    Формирует сообщение:
      - Если total_weight == 0: красное мясо не потреблялось.
      - Если total_weight > 700 г: предупреждение о превышении нормы.
      - Иначе: "Потреблено X г из 700 г, что соответствует Y порциям из 3."
    """
    if total_weight == 0:
        return "Вы не потребляли красное мясо за неделю. Рекомендуем добавить его в рацион."
    if total_weight > 700:
        return f"Вы превысили рекомендуемую норму красного мяса (700 г). Потреблено {total_weight:.0f} г. Пожалуйста, снизьте потребление."
    
    return f"Потреблено {total_weight:.0f} г из 700 г, что соответствует {portions:.1f} порциям из 3 (общий белок: {total_protein:.1f} г)."

# --- Часть 2. Накопление данных по неделям (сброс каждую неделю) ---

# In-memory хранилище данных: red_meat_data = { user_id: { date: (weight, protein) } }
red_meat_data = {}

def add_or_update_daily_red_meat(user_id, weight, protein):
    """
    Добавляет или обновляет данные за текущий день для пользователя.
    """
    today = datetime.now().date()
    if user_id not in red_meat_data:
        red_meat_data[user_id] = {}
    red_meat_data[user_id][today] = (weight, protein)
    logging.debug(f"Обновлены данные для {user_id} за {today}: вес {weight} г, белок {protein:.1f} г")

def get_weekly_red_meat(user_id):
    """
    Суммирует данные за текущую неделю (с понедельника).
    Возвращает суммарный вес (г) и суммарный белок (г).
    """
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    total_weight = 0.0
    total_protein = 0.0
    if user_id in red_meat_data:
        for date, (w, p) in red_meat_data[user_id].items():
            if date >= start_of_week:
                total_weight += w
                total_protein += p
    return total_weight, total_protein

# --- Пример автономного тестирования ---
if __name__ == "__main__":
    # Пример списка продуктов из PDF.
    # Формат: (название, вес_строкой, белок_в_граммах или None)
    sample_products = [
        ("Говядина нежирная", "150 г", "38"),  # извлечено: 38 г белка
        ("Свинная вырезка", "200 г", "60"),      # извлечено: 60 г белка
        ("Утятина", "120 г", "30"),             # извлечено: 30 г белка
        ("Куриное филе", "100 г", "20"),         # не относится к красному мясу
        ("Баранина", "100 г", "27"),             # извлечено: 27 г белка
        ("Яблоко", "120 г", None)                # не относится к красному мясу
    ]
    user_id = "test_user"
    
    # Расчет по текущей сессии (например, из одного PDF)
    session_weight, session_protein, session_portions = handle_red_meat(sample_products)
    message = red_meat_message(session_weight, session_protein, session_portions)
    print("Результаты сессии:")
    print(f"Общий вес: {session_weight:.0f} г, Белок: {session_protein:.1f} г, Порций: {session_portions:.2f}")
    print(message)
    
    # Обновляем данные за сегодня для пользователя
    add_or_update_daily_red_meat(user_id, session_weight, session_protein)
    
    # Выводим недельные итоги
    weekly_weight, weekly_protein = get_weekly_red_meat(user_id)
    weekly_portions = weekly_protein / 25.0 if weekly_protein > 0 else 0.0
    print("\nНедельные итоги:")
    print(f"Потреблено: {weekly_weight:.0f} г из 700 г, Белок: {weekly_protein:.1f} г (≈{weekly_portions:.2f} порций из 3)")