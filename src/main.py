import sys
import os
import re
import logging
import tempfile
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import config
import auth
import fatsecret_api
import product_filters
import vegetable_fruit_filters
import omega3_google_tracker
import usda_omega3
import red_meat_tracker
import red_meat_google_tracker
from csv_parser import extract_products_from_csv

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def is_header(product_name: str) -> bool:
    """
    Проверяет, является ли строка заголовком (например, содержащим слова "кал", "жир", "белк" и т.д.).
    """
    header_keywords = ["кал", "жир", "углев", "клетч", "сахар", "белк", "натри", "холес", "калий"]
    return any(keyword in product_name.lower() for keyword in header_keywords)

def is_red_meat(product_name):
    """
    Определяет, является ли продукт красным мясом (например, говядина, свинина, баранина, утятина).
    Удаляются цифры, запятые и точки, затем проверяются ключевые слова.
    """
    red_meat_keywords = ["говядин", "свин", "баран", "утят"]
    clean_name = re.sub(r'[\d,\.]', '', product_name).lower()
    result = any(keyword in clean_name for keyword in red_meat_keywords)
    logging.debug(f"is_red_meat('{product_name}') -> {result} (clean: '{clean_name}')")
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_chat.id
    logging.info(f"/start: Получен запрос от пользователя {user_id}.")
    await update.message.reply_text("Бот готов! Отправьте ссылку на CSV-файл.")

async def handle_csv_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()
    logging.debug(f"handle_csv_link: получена ссылка: {text}")
    await update.message.reply_text("Обработчик CSV-ссылки вызван!")
    
    if not re.search(r'\.csv(\?.*)?$', text, re.IGNORECASE):
        await update.message.reply_text("Пожалуйста, отправьте ссылку на CSV-файл.")
        return

    try:
        logging.debug("Скачиваем CSV по ссылке...")
        response = requests.get(text, timeout=10)
        response.raise_for_status()
        logging.debug("CSV успешно скачан.")
    except Exception as e:
        logging.error(f"Ошибка скачивания CSV: {e}")
        await update.message.reply_text("Не удалось скачать CSV.")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
        tmp_file.write(response.content)
        tmp_file_path = tmp_file.name

    logging.info(f"CSV-файл сохранён во временный файл: {tmp_file_path}")
    products = extract_products_from_csv(tmp_file_path)
    logging.debug(f"handle_csv_link: Извлечено {len(products)} записей из CSV.")
    os.unlink(tmp_file_path)
    await process_products(update, products)

async def process_products(update: Update, products) -> None:
    if not products:
        await update.message.reply_text("Ошибка обработки данных из CSV.")
        return

    # Расчет молочной продукции
    dairy_products = product_filters.filter_dairy_products(products, api_categories={})
    total_calcium = sum(
        fatsecret_api.get_calcium_for_product(
            product, 
            config.MASTER_ACCESS_TOKEN, 
            config.MASTER_ACCESS_TOKEN_SECRET, 
            fatsecret_api.parse_weight(weight)
        )
        for product, weight, *_ in dairy_products
    )
    logging.debug(f"process_products: Общий кальций: {total_calcium} мг.")

    # Расчет растительной продукции
    total_weight, plant_message = vegetable_fruit_filters.handle_vegetables_and_fruits(products)
    logging.debug(f"process_products: Растительная продукция: {total_weight} г, сообщение: {plant_message}")

    # Формируем список для омега‑3: исключаем красное мясо и заголовки, используя локальную функцию is_header
    omega3_products = [
        (p, w) for (p, w, *_) in products if not usda_omega3.is_red_meat_local(p) and not is_header(p)
    ]
    logging.debug(f"process_products: Осталось {len(omega3_products)} записей для омега‑3.")
    total_omega3_daily = sum(
        usda_omega3.get_omega3_for_product(p, fatsecret_api.parse_weight(w))
        for p, w in omega3_products
    )
    logging.debug(f"process_products: Общая омега‑3: {total_omega3_daily} г.")
    omega3_google_tracker.add_or_update_daily_omega(update.message.chat_id, total_omega3_daily * 1000)
    weekly_omega3_g = omega3_google_tracker.get_weekly_omega(update.message.chat_id) / 1000

    # Расчет красного мяса
    red_meat_weight, red_meat_protein, red_meat_portions = red_meat_tracker.handle_red_meat(products)
    logging.debug(f"process_products: Красное мясо: вес={red_meat_weight} г, белок={red_meat_protein} г, порции={red_meat_portions}.")
    red_meat_google_tracker.add_or_update_daily_red_meat(update.message.chat_id, red_meat_weight, red_meat_protein)
    weekly_red_weight, weekly_red_protein = red_meat_google_tracker.get_weekly_red_meat(update.message.chat_id)
    weekly_red_portions = weekly_red_protein / 25.0 if weekly_red_protein > 0 else 0.0

    await update.message.reply_text(f"Кальций: {total_calcium:.1f} мг")
    await update.message.reply_text(f"Растительная продукция: {total_weight:.1f} г\n{plant_message}")
    await update.message.reply_text(f"Омега‑3 сегодня: {total_omega3_daily:.2f} г")
    await update.message.reply_text(f"Омега‑3 за неделю: {weekly_omega3_g:.2f} г")
    await update.message.reply_text(f"Красное мясо за неделю: {weekly_red_weight:.1f} г из 700 г")
    await update.message.reply_text(f"Белок из красного мяса: {weekly_red_protein:.1f} г (≈{weekly_red_portions:.1f} порций)")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip() if update.message and update.message.text else ""
    logging.debug(f"handle_text: получено сообщение: {text}")
    if re.search(r'\.csv(\?.*)?$', text, re.IGNORECASE):
        await handle_csv_link(update, context)
    else:
        await echo_handler(update, context)

async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        text = update.message.text.strip()
        logging.debug(f"echo_handler: получено сообщение: {text}")
        await update.message.reply_text(f"Эхо: {text}")
    else:
        logging.debug("echo_handler: Нет текста в сообщении.")

def main():
    application = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.ALL, handle_text))
    application.run_polling()

if __name__ == "__main__":
    main()